"""Crew orchestration for email reading and draft generation"""
from crewai import Crew, Process
from agents.email_reader import create_email_reader_agent
from agents.draft_generator import create_draft_generator_agent
from tasks.email_tasks import create_email_reading_task, create_draft_generation_task


def process_email(email_content):
    """
    Process a single email and generate a draft response
    Args:
        email_content: Dictionary containing email details (from, subject, date, body)
    Returns:
        Generated email draft
    """
    # Create agents
    email_reader = create_email_reader_agent()
    draft_generator = create_draft_generator_agent()
    
    # Create reading task
    reading_task = create_email_reading_task(email_reader, email_content)
    
    # Create draft task - it will use the reading task's output via context
    draft_task = create_draft_generation_task(
        draft_generator, 
        "Use the email analysis from the previous task to generate the draft"
    )
    
    # Link tasks: reading_task output feeds into draft_task
    draft_task.context = [reading_task]
    
    # Create crew with agents and tasks
    crew = Crew(
        agents=[email_reader, draft_generator],
        tasks=[reading_task, draft_task],
        process=Process.sequential,
        memory=False,
        verbose=True
    )
    
    # Execute crew
    result = crew.kickoff()
    
    return result

