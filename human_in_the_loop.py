from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.prebuilt import ToolInvocation
import json
from langchain_core.messages import FunctionMessage
from langgraph.graph import MessageGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv

load_dotenv()

tools = [TavilySearchResults(max_results=1)]
tool_executor = ToolExecutor(tools)

model = ChatOpenAI(temperature=0, streaming=True)
functions = [convert_to_openai_function(t) for t in tools]
model = model.bind_functions(functions)

def should_continue(messages):
    last_message = messages[-1]
    # If there is no function call, then we finish
    if "function_call" not in last_message.additional_kwargs:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define the function that calls the model
def call_model(messages):
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return response


# Define the function to execute tools
def call_tool(messages):
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    action = ToolInvocation(
        tool=last_message.additional_kwargs["function_call"]["name"],
        tool_input=json.loads(
            last_message.additional_kwargs["function_call"]["arguments"]
        ),
    )
    # We call the tool_executor and get back a response
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(content=str(response), name=action.tool)
    # We return a list, because this will get added to the existing list
    return function_message

workflow = MessageGraph()

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    # This means these are the edges taken after the `agent` node is called.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # Finally we pass in a mapping.
    # The keys are strings, and the values are other nodes.
    # END is a special node marking that the graph should finish.
    # What will happen is we will call `should_continue`, and then the output of that
    # will be matched against the keys in this mapping.
    # Based on which one it matches, that node will then be called.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END,
    },
)

# We now add a normal edge from `tools` to `agent`.
# This means that after `tools` is called, `agent` node is called next.
workflow.add_edge("action", "agent")

memory = SqliteSaver.from_conn_string(":memory:")

app = workflow.compile(checkpointer=memory, interrupt_before=["action"])

inputs = [HumanMessage(content="hi! I'm bob")]
for event in app.stream(inputs, {"configurable": {"thread_id": "2"}}):
    for k, v in event.items():
        if k != "__end__":
            print(v)
            
inputs = [HumanMessage(content="what's the weather in sf now?")]
for event in app.stream(inputs, {"configurable": {"thread_id": "2"}}):
    for k, v in event.items():
        if k != "__end__":
            print(v)
            
for event in app.stream(None, {"configurable": {"thread_id": "2"}}):
    for k, v in event.items():
        if k != "__end__":
            print(v)