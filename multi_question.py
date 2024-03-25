import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, MessageGraph
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, AIMessage
from typing import List 

from dotenv import load_dotenv

load_dotenv()

@tool
def save_email(email: str):
    """Stores the users email."""
    print(email)
    return "Email saved!"
    
def invoke_save_email(state: List[BaseMessage]):
    print(state)
    tool_calls = state[-1].additional_kwargs.get("tool_calls", [])
    func_call = None
    
    for tool_call in tool_calls:
        if tool_call.get("function").get("name") == "save_email":
            func_call = tool_call                                            
    
    if func_call is None:
        raise Exception("No func found.")
          
    print(func_call)
    # TODO - execute the fuction call   
    res = "Email saved!"
                                                 
    return ToolMessage(
        tool_call_id=func_call.get("id"),
        content=res
    )

def invoke_model(state: List[BaseMessage]):
    return model_with_tools.invoke(state)

def invoke_music_model(state: List[BaseMessage]):
    return music_model.invoke(state)

def user_node(state: List[BaseMessage]):
    user_input = input("Enter more info:")
    state.append(HumanMessage(content=user_input))
    return state

model = ChatOpenAI(model="gpt-4-0125-preview",temperature=0)
model_with_tools = model.bind(tools=[convert_to_openai_tool(save_email)])

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a helpful assistant, your only goal is to ask the user for their email, do not ask anything else. Only call a function if they have entered an email.")
])

output_parser = StrOutputParser()

get_email_chain = prompt | model_with_tools | output_parser


music_model = ChatOpenAI(model="gpt-4-0125-preview",temperature=0)
music_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an expert on contempory music, your goal is to ask the user for their favorite song. Only call a function if they have entered a song.")
])

music_chain = music_prompt | music_model | output_parser




graph = MessageGraph()

graph.add_node("oracle", invoke_model)
graph.add_node("user", user_node)
graph.add_node("music", invoke_music_model)
graph.add_edge("user", "oracle")
graph.add_node("save_email", invoke_save_email)
graph.add_edge("save_email", "music")


def music_router(state: List[BaseMessage]):
    if state and isinstance(state[-1], AIMessage):
        return "user"
    else:
        return "music"

def router(state: List[BaseMessage]):
    print(state)
    tool_calls = state[-1].additional_kwargs.get("tool_calls", [])
    if len(tool_calls):
        return "save_email"
    else:
        return "user"
    
graph.add_conditional_edges("oracle", router, {
    "save_email": "save_email",
    "user": "user",
})

graph.add_conditional_edges("music", music_router, {
    "music": "music",
    "user": "user"
})

graph.set_entry_point("user")

app = graph.compile()

res = app.invoke(HumanMessage(content="I wish to enter the contest"))

print(res)