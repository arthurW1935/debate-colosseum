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

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    
    # 1. Allow the model to use tools if any are provided
    if tools:
        bound_tools = []
        for t in tools:
            t_name = getattr(t, "name", getattr(t, "__name__", ""))
            if t_name == "doc_retrieval":
                class DocRetrievalInput(BaseModel):
                    query: str = Field(..., description="The query to search the documents for.")
                
                def doc_retrieval_wrapper(query: str):
                    return t(query, getattr(state, "retriever", None))
                
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
            messages.append(response)
            
            if not response.tool_calls:
                break
                
            for tc in response.tool_calls:
                tool_func = next((t for t in bound_tools if getattr(t, "name", getattr(t, "__name__", "")) == tc["name"]), None)
                if tool_func:
                    try:
                        args = dict(tc["args"])
                        if hasattr(tool_func, "invoke"):
                            invoke_tool = traceable(name=f"{role}_exec_tool_{tc['name']}")(tool_func.invoke)
                            result = invoke_tool(args)
                        else:
                            invoke_tool = traceable(name=f"{role}_exec_tool_{tc['name']}")(tool_func)
                            result = invoke_tool(**args)
                        messages.append(ToolMessage(tool_call_id=tc["id"], content=str(result), name=tc["name"]))
                    except Exception as e:
                        messages.append(ToolMessage(tool_call_id=tc["id"], content=f"Tool error: {e}", name=tc["name"]))
                else:
                    messages.append(ToolMessage(tool_call_id=tc["id"], content="Tool not found.", name=tc["name"]))
                    
        # Instruct model to output the final analysis
        messages.append(HumanMessage(content="Now, please provide your final analysis strictly adhering to the required schema."))

    # 2. Extract structured output with retry logic
    structured_model = model.with_structured_output(ExpertAnalysis)
    invoke_structured = traceable(name=f"{role}_structured_output_invoke")(structured_model.invoke)
    
    try:
        return invoke_structured(messages)
    except Exception as e:
        # Retry exactly once
        messages.append(HumanMessage(content=f"Your previous output failed schema validation: {e}. Please correct it and strictly adhere to the schema."))
        invoke_structured_retry = traceable(name=f"{role}_structured_output_retry")(structured_model.invoke)
        return invoke_structured_retry(messages)
