from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import END, MessageGraph

from dotenv import load_dotenv

load_dotenv()

def print_state(messages: list):
    print("Print Statement:")
    for message in messages:
        print(message)
        print("------")


model = ChatOpenAI(temperature=0)

graph = MessageGraph()

graph.add_node("oracle", model)
graph.add_node("print_statement", print_state)


graph.add_edge("oracle", "print_statement")
graph.add_edge("print_statement", END)

graph.set_entry_point("oracle")
app = graph.compile()

print(app.get_graph().print_ascii())

res = app.invoke(HumanMessage("What is 1 + 1?"))

print(res)