"""Draft Generator Agent - Creates email draft responses"""
from crewai import Agent
from langchain_openai import ChatOpenAI

def create_draft_generator_agent():
    """Create an agent specialized in generating professional email drafts"""
    return Agent(
        role='Email Draft Writer',
        goal='Generate professional, clear, and appropriate email draft responses based on the original email content',
        backstory="""You are a professional email communication expert with extensive 
        experience in crafting clear, concise, and professional email responses. 
        You understand tone, context, and the importance of addressing all points 
        raised in the original email while maintaining professionalism.""",
        verbose=False, # Set to True to see the agent's internal state
        allow_delegation=False,
        llm=ChatOpenAI(model_name="gpt-4", temperature=0.7)
    )

