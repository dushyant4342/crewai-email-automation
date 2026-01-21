"""Tasks for email reading and draft generation"""
from crewai import Task

def create_email_reading_task(email_reader_agent, email_content):
    """Create a task for reading and analyzing an email"""
    return Task(
        description=f"""
        Read and analyze the following email:
        
        From: {email_content.get('from', 'Unknown')}
        Subject: {email_content.get('subject', 'No Subject')}
        Date: {email_content.get('date', 'Unknown')}
        
        Content:
        {email_content.get('body', 'No content')}
        
        Extract and summarize:
        1. Who is the sender?
        2. What is the main purpose of this email?
        3. What are the key points that need to be addressed?
        4. What is the tone and urgency level?
        5. What information is needed to craft an appropriate response?
        """,
        agent=email_reader_agent,
        expected_output="A structured analysis containing sender info, main purpose, key points, tone, urgency, and required information for response"
    )

def create_draft_generation_task(draft_generator_agent, email_analysis):
    """Create a task for generating an email draft"""
    return Task(
        description=f"""
        Based on the following email analysis, generate a professional email draft response:
        
        {email_analysis}
        
        The draft should:
        1. Be professional and appropriate in tone
        2. Address all key points from the original email
        3. Be clear and concise
        4. Include a proper greeting and closing
        5. Match the urgency level of the original email
        """,
        agent=draft_generator_agent,
        expected_output="A complete email draft response ready to send, including subject line, greeting, body, and closing"
    )

