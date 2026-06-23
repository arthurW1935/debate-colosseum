from typing import Any, Sequence
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from src.schemas import ExpertAnalysis, GraphState
from src.config import get_chat_model

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
    if state.context_docs:
        user_content += "\n[Supporting Context]\n" + "\n".join(state.context_docs)
        
    if turn == 2:
        user_content += "\n\n[Peers' Turn 1 Analyses]\n"
        for peer_role, analysis in state.turn1_analyses.items():
            if peer_role != role:
                user_content += f"- {peer_role}: {analysis.recommendation.value} (Confidence: {analysis.confidence})\n"
                user_content += f"  Summary: {analysis.summary}\n"
                
        if state.disagreement_report_t1:
            user_content += f"\n[Moderator's Disagreement Report]\nScore: {state.disagreement_report_t1.score}\nSummary: {state.disagreement_report_t1.summary}\n"
            
        user_content += "\nPlease populate `dissent_notes` if you disagree with any peer's assumptions."

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    
    # 1. Allow the model to use tools if any are provided
    if tools:
        model_with_tools = model.bind_tools(tools)
        for _ in range(5):  # Max 5 tool call turns
            response = model_with_tools.invoke(messages)
            messages.append(response)
            
            if not response.tool_calls:
                break
                
            for tc in response.tool_calls:
                tool_func = next((t for t in tools if t.name == tc["name"]), None)
                if tool_func:
                    try:
                        result = tool_func.invoke(tc["args"])
                        messages.append(ToolMessage(tool_call_id=tc["id"], content=str(result), name=tc["name"]))
                    except Exception as e:
                        messages.append(ToolMessage(tool_call_id=tc["id"], content=f"Tool error: {e}", name=tc["name"]))
                else:
                    messages.append(ToolMessage(tool_call_id=tc["id"], content="Tool not found.", name=tc["name"]))
                    
        # Instruct model to output the final analysis
        messages.append(HumanMessage(content="Now, please provide your final analysis strictly adhering to the required schema."))

    # 2. Extract structured output with retry logic
    structured_model = model.with_structured_output(ExpertAnalysis)
    
    try:
        return structured_model.invoke(messages)
    except Exception as e:
        # Retry exactly once
        messages.append(HumanMessage(content=f"Your previous output failed schema validation: {e}. Please correct it and strictly adhere to the schema."))
        return structured_model.invoke(messages)
