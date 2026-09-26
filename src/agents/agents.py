import os
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools.tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# Model Inititalization

llm = ChatOllama(
    model="llama3.2",
    temperature=0.5,
)

# 1st Agent: Search Agent
def build_search_agent():
    return create_agent(
        model = llm,
        tools = [web_search],

    )


# 2nd Agent: Reader Agent
def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url],

    )

# writer_chain

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a research report on the topic below.
    
Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs from the research)

Be detailed,factual and proffessionl."""),
])
writer_chain = writer_prompt | llm | StrOutputParser()



# critic_chain

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and costructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.
    
Report:
{report}

Respond in this exact format:

Score: X/10

Strength:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
