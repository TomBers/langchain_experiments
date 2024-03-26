from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StepState(TypedDict):
    state: str
    messages: List[str]
    
class AgentState(TypedDict):
    steps: List[StepState]
    

def add_message(state: AgentState) -> AgentState:
    state["steps"].append(AgentState(state="updated", messages="updated"))
    return state
    

workflow = StateGraph(AgentState)


workflow.add_node("add_message", add_message)

workflow.add_edge("add_message", END)

workflow.set_entry_point("add_message")

app = workflow.compile()

print(app.get_graph().print_ascii())

res = app.invoke(AgentState(steps=[AgentState(state="start", messages=["start"])]))

print(res)