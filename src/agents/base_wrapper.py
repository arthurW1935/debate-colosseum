from typing import Any, Sequence
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.schemas import ExpertAnalysis, GraphState
from src.config import get_chat_model
from langsmith import traceable
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

@traceable(name="call_agent_with_retry")
def call_agent_with_retry(
    state: GraphState,
    role: str,
    system_prompt: str,
    tools: Sequence[Any],
    turn: int = 1
) -> ExpertAnalysis:
    """
    Executes an LLM call with tool usage, outputs a structured ExpertAnalysis,
    and catches validation errors to retry exactly once.
    """
    model = get_chat_model(temperature=0.0)
    
    # Build initial user content
    user_content = f"Problem Statement:\n{state.problem_statement}\n"
    
    # DO NOT dump context_docs directly to save tokens! Force agent to use tools.
    if state.context_docs:
        user_content += "\n[Context Documents are available. You MUST use the `doc_retrieval` tool to search through them.]\n"
        
    if turn == 2:
        user_content += "\n\n[Peers' Turn 1 Analyses]\n"
        for peer_role, analysis in state.turn1_analyses.items():
            if peer_role != role:
                user_content += f"- {peer_role}: {analysis.recommendation.value} (Confidence: {analysis.confidence})\n"
                user_content += f"  Summary: {analysis.summary}\n"
                
        if state.disagreement_report_t1:
            user_content += f"\n[Moderator's Disagreement Report]\nScore: {state.disagreement_report_t1.score}\nSummary: {state.disagreement_report_t1.summary}\n"
            
        user_content += "\nPlease populate `dissent_notes` using the strict format `[Peer Role]: [Specific disagreement]` if you disagree with any peer's assumptions."

    # Feedback round: inject the human's feedback and the memo being revised
    if state.current_feedback_text:
        user_content += "\n\n[FEEDBACK ROUND — Human Reviewer Note]\n"
        user_content += f"{state.current_feedback_text}\n"
        user_content += "\nYou MUST address the above feedback directly. Explain any changes in the `feedback_context` field.\n"
        if state.final_memo:
            user_content += f"\n[Current Decision Memo Being Revised]\n"
            user_content += f"Recommendation: {state.final_memo.recommendation.value}\n"
            user_content += f"Confidence: {state.final_memo.confidence}\n"
            user_content += f"Executive Summary: {state.final_memo.executive_summary}\n"

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    
    # 1. Allow the model to use tools if any are provided
    if tools:
        bound_tools = []
        for t in tools:
            t_name = getattr(t, "name", getattr(t, "__name__", ""))
            if t_name == "doc_retrieval":
                class DocRetrievalInput(BaseModel):
                    query: str = Field(..., description="The query to search the documents for.")
                
                def doc_retrieval_wrapper(query: str, _t=t):
                    # Use _t to avoid Python late-binding loop variable capture
                    if hasattr(_t, "invoke"):
                        # Just in case doc_retrieval was passed as a StructuredTool already
                        return _t.invoke({"query": query, "retriever": getattr(state, "retriever", None)})
                    return _t(query, getattr(state, "retriever", None))
                
                bound_tools.append(StructuredTool.from_function(
                    func=doc_retrieval_wrapper,
                    name="doc_retrieval",
                    description="Retrieves top 8 candidates using cosine similarity, then reranks to top 4 using a cross-encoder.",
                    args_schema=DocRetrievalInput
                ))
            else:
                bound_tools.append(t)
                
        model_with_tools = model.bind_tools(bound_tools)
        for i in range(2):  # Max 2 tool call turns
            print(f"[{role.upper()}] Turn {i+1}: Waiting for LLM response...")
            
            invoke_llm = traceable(name=f"{role}_tool_llm_invoke_turn_{i+1}")(model_with_tools.invoke)
            response = invoke_llm(messages)
            
            print(f"[{role.upper()}] Turn {i+1}: LLM response received. Tool calls: {len(response.tool_calls)}")
            
            # Strip massive Gemini thought blocks to prevent token bloat in subsequent turns
            if hasattr(response, "additional_kwargs"):
                keys_to_remove = [k for k in response.additional_kwargs if k.startswith("__gemini")]
                for k in keys_to_remove:
                    response.additional_kwargs.pop(k, None)
                    
            messages.append(response)
            
            # Check if the model decided to call tools
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    # Find the tool
                    tool_func = None
                    for t in bound_tools:
                        if getattr(t, "name", getattr(t, "__name__", "")) == tc["name"]:
                            tool_func = t
                            break
                            
                    if tool_func:
                        try:
                            args = dict(tc["args"])
                            if hasattr(tool_func, "invoke"):
                                invoke_tool = traceable(name=f"{role}_exec_tool_{tc['name']}")(tool_func.invoke)
                                result = invoke_tool(args)
                            else:
                                invoke_tool = traceable(name=f"{role}_exec_tool_{tc['name']}")(tool_func)
                                result = invoke_tool(**args)
                            tool_content = str(result)
                            if not tool_content.strip():
                                tool_content = "No output"
                            messages.append(ToolMessage(tool_call_id=tc["id"], content=tool_content, name=tc["name"]))
                        except Exception as e:
                            messages.append(ToolMessage(tool_call_id=tc["id"], content=f"Tool error: {e}", name=tc["name"]))
                    else:
                        messages.append(ToolMessage(tool_call_id=tc["id"], content="Tool not found.", name=tc["name"]))
            else:
                # Model didn't use tools, break the loop
                if not response.content:
                    # Prevent Vertex AI crash: "must include at least one parts field"
                    # If content is empty (e.g. after stripping thought blocks), give it dummy text.
                    response.content = "Analysis complete."
                break
                    
        # Instruct model to output the final analysis
        messages.append(HumanMessage(content="Now, please provide your final analysis strictly adhering to the required schema."))

    # 2. Extract structured output with retry logic
    structured_model = model.with_structured_output(ExpertAnalysis)
    invoke_structured = traceable(name=f"{role}_structured_output_invoke")(structured_model.invoke)
    
    try:
        result = invoke_structured(messages)
        if result is None:
            raise ValueError("Model failed to invoke the structured output function call.")
        result.round = str(turn) if turn in [1, 2] else "feedback"
        return result
    except Exception as e:
        # Retry exactly once
        messages.append(HumanMessage(content=f"Your previous output failed schema validation or was missing the required tool call: {e}. Please strictly adhere to the JSON schema format by using the required tool call."))
        invoke_structured_retry = traceable(name=f"{role}_structured_output_retry")(structured_model.invoke)
        try:
            result = invoke_structured_retry(messages)
            if result is None:
                raise ValueError("Model failed to invoke the structured output function call on retry.")
            result.round = str(turn) if turn in [1, 2] else "feedback"
            return result
        except Exception as retry_e:
            from src.schemas import Recommendation
            # Provide a safe fallback to prevent the entire graph from crashing
            return ExpertAnalysis(
                agent_role=role,
                round=str(turn) if turn in [1, 2] else "feedback",
                recommendation=Recommendation.PROCEED_WITH_CAUTION,
                confidence=0.5,
                summary=f"Fallback triggered: Model failed to format output correctly. Error: {retry_e}",
                key_assumptions=["Model formatting failure"],
                supporting_evidence=[],
                risks=[],
                dissent_notes="Failed to extract structural output from the LLM."
            )
