"""
Email Processing Workflow with Supervisor Pattern:
1. Email Reader Agent → reads email
2. Supervisor Agent → decides tool (web/rag/db) and uses it
3. Draft Writer Agent → writes response
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import sys
import os
import datetime
from utils.email_fetcher import fetch_emails
from utils.draft_creator import create_gmail_draft
from serpapi import GoogleSearch

# SerpAPI key (set SERPAPI_API_KEY in .env)
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# Fix encoding for Windows console to handle emoji and special characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# ========== TOOLS ==========
@tool("web_search_tool")
def web_search(query: str) -> str:
    """Web search via SerpAPI GoogleSearch."""
    if not SERPAPI_API_KEY:
        return "[WEB SEARCH ERROR] SERPAPI_API_KEY not set"
    try:
        search = GoogleSearch(
            {
                "q": query.strip(),
                "api_key": SERPAPI_API_KEY,
                "num": 2,
            }
        )
        results = search.get_dict()
        # Return top results briefly
        organic = results.get("organic_results", [])[:3]
        snippets = []
        for item in organic:
            title = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            snippets.append(f"- {title} | {link} | {snippet}")
        if not snippets:
            return "[WEB SEARCH] No results"
        return "[WEB SEARCH via SerpAPI]\\n" + "\\n".join(snippets)
    except Exception as e:
        return f"[WEB SEARCH ERROR] {e}"

@tool("rag_tool")
def rag_search(query: str) -> str:
    """Simulated RAG over internal docs."""
    return f"[RAG] Internal knowledge for: {query}"

@tool("db_call_tool")
def db_call(query: str) -> str:
    """Simulated DB/API call for structured data."""
    return f"[DB] Queried database with: {query}"

# ========== AGENTS ==========
email_reader = Agent(
    role="Email Reader",
    goal="Read and analyze emails to extract key information",
    backstory="You are expert at understanding email content and extracting important details.",
    verbose=False
)

supervisor = Agent(
    role="Supervisor",
    goal="Decide which tool to use and gather information",
    backstory="You analyze queries and route to the right tool (web/rag/db).",
    tools=[web_search, rag_search, db_call],
    verbose=False
)

draft_writer = Agent(
    role="Draft Writer",
    goal="Write professional email responses",
    backstory="You are a professional email writer who creates clear, helpful responses.",
    verbose=False
)

# ========== WORKFLOW ==========
def process_email(email_data: dict) -> str:
    """Process email through 3-agent workflow"""
    today = datetime.date.today().isoformat()
    # Task 1: Read email
    read_task = Task(
        description=f"""
        Read and analyze this email:
        From: {email_data.get('from', 'Unknown')}
        Subject: {email_data.get('subject', 'No Subject')}
        Body: {email_data.get('body', '')[:500]}
        
        Extract: main question, key points, what information is needed.
        """,
        agent=email_reader,
        expected_output="Analysis of email content and information needs"
    )
    
    # Task 2: Supervisor decides tool and gathers info
    supervisor_task = Task(
        description=f"""
        Today is {today}.
        Based on the email analysis from previous task:
        
        1. Decide which tool is best:
           - web_search_tool → for public/latest info
           - rag_search_tool → for internal/company docs
           - db_call_tool → for database queries
        
        2. Use that tool to gather information needed to answer the email.
        
        3. Provide the gathered information clearly.
        """,
        agent=supervisor,
        expected_output="Information gathered using the chosen tool"
    )
    supervisor_task.context = [read_task]
    
    # Task 3: Write draft response
    draft_task = Task(
        description=f"""
        Original email:
        From: {email_data.get('from', 'Unknown')}
        Subject: {email_data.get('subject', 'No Subject')}
        
        Using:
        1. Email analysis from Task 1
        2. Information gathered from Task 2
        
        Write a professional email response that answers the sender's question.
        Keep the subject/thread aligned with the original email (reply style).
        """,
        agent=draft_writer,
        expected_output="Professional email draft response"
    )
    draft_task.context = [read_task, supervisor_task]
    
    # Create crew
    crew = Crew(
        agents=[email_reader, supervisor, draft_writer],
        tasks=[read_task, supervisor_task, draft_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew.kickoff()

# ========== MAIN ==========
if __name__ == "__main__":
    # Fetch latest email
    emails = fetch_emails(limit=1)
    
    if not emails:
        print("No emails found!")
    else:
        email = emails[0]
        print("=" * 70)
        print(f"Processing Email: {email.get('subject', 'No Subject')}")
        print("=" * 70)
        
        result = process_email(email)
        print("\n" + "=" * 70)
        print("DRAFT RESPONSE:")
        print("=" * 70)
        print(result)

        # Create threaded draft in Gmail (replies in the same email thread via headers)
        try:
            create_gmail_draft(str(result), email)
            print("\n✓ Draft created successfully in Gmail Drafts (same thread).")
        except Exception as e:
            print(f"\n⚠ Could not create Gmail draft: {e}")
