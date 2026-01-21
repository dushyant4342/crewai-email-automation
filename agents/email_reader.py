"""Email Reader Agent - Reads and analyzes emails"""
from crewai import Agent
from langchain_openai import ChatOpenAI

def create_email_reader_agent():
    """Create an agent specialized in reading and understanding emails"""
    return Agent(
        role='Email Reader',
        goal='Read and analyze emails to extract key information, sender details, subject, and content',
        backstory="""You are an expert email analyst with years of experience 
        in understanding email communications. You excel at extracting important 
        information from emails, identifying the sender's intent, and summarizing 
        the key points that need to be addressed in a response.""",
        verbose=False, # Set to True to see the agent's internal state
        allow_delegation=False,
        llm=ChatOpenAI(model_name="gpt-4", temperature=0.7)
    )

