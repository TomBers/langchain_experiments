from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessageGraph
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from typing import List 

from dotenv import load_dotenv

load_dotenv()

def user_node(state: List[BaseMessage]):
    print(state)
    user_input = input("Enter more info:")
    state.append(HumanMessage(content=user_input))
    return state



music_model = ChatOpenAI(temperature=0)
music_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an expert on contempory music, your goal is to ask the user for their favorite song. Only call a function if they have entered a song.")
])

output_parser = StrOutputParser()

music_chain = music_prompt | music_model | output_parser

graph = MessageGraph()

graph.add_node("oracle", music_model)
graph.add_node("user", user_node)
graph.add_edge("user", "oracle")

def router(state: List[BaseMessage]):
    if len(state) > 7:
        return "end"
    else:
        return "user"

graph.add_conditional_edges("oracle", router, {
    "end": END,
    "user": "user",
})


graph.set_entry_point("oracle")

app = graph.compile()

messages = [
    SystemMessage(content="Lets talk about music. If the user asks for help, ask them for their favorite song."),
    HumanMessage(content="What do you want to talk about?"),
]


res = app.invoke(messages)

print(res)


    
    