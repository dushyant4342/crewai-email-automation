"""
LangGraph Supervisor Pattern - Dynamic Agent Orchestration

This shows how LangGraph allows true dynamic routing:
- Supervisor decides which agent to use
- Only that agent's node executes (others are skipped)
- Supervisor frames final answer using agent's output

Key difference from CrewAI:
- LangGraph: Dynamic graph, supervisor can route to any node at runtime
- CrewAI: Fixed tasks, routing simulated via task descriptions
"""

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, Literal
import operator
from dotenv import load_dotenv
import os

load_dotenv()

# ========== STATE DEFINITION ==========
class AgentState(TypedDict):
    """State that flows through the graph"""
    messages: Annotated[list, operator.add]  # List of messages
    query: str  # Original user query
    route: str  # Supervisor's decision: "WEB", "RAG", or "DB"
    agent_output: str  # Output from the chosen agent
    final_answer: str  # Supervisor's final framed answer


# ========== TOOLS (same as CrewAI example) ==========
def web_search_tool(query: str) -> str:
    """Search the web for information. Use this for general/latest information."""
    # Simulated web search - replace with real API
    return f"[WEB SEARCH] Best public info about: {query}"


def rag_search_tool(query: str) -> str:
    """Search internal knowledge base/documents. Use this for company-specific info."""
    # Simulated RAG - replace with real vector DB
    return f"[RAG] Internal knowledge for: {query}"


def db_call_tool(query: str) -> str:
    """Query database/API for structured data."""
    # Simulated DB call - replace with real API
    return f"[DB] Queried database with: {query}"


# ========== LLM INITIALIZATION ==========
llm = ChatOpenAI(model="gpt-4", temperature=0)


# ========== NODES ==========
def supervisor_node(state: AgentState) -> AgentState:
    """
    Supervisor analyzes query and decides which agent to use.
    This is like a router node.
    """
    query = state["query"]
    
    messages = [
        SystemMessage(content="""You are a supervisor that routes queries to the right agent.
        
        Analyze the query and decide which ONE agent should handle it:
        - WEB → for public/latest info, general knowledge
        - RAG → for internal docs, company-specific knowledge  
        - DB → for database queries, structured data
        
        Return ONLY: WEB, RAG, or DB"""),
        HumanMessage(content=f"User query: {query}\n\nWhich agent should handle this? Return only: WEB, RAG, or DB")
    ]
    
    response = llm.invoke(messages)
    route = response.content.strip().upper()
    
    # Ensure valid route
    if route not in ["WEB", "RAG", "DB"]:
        route = "WEB"  # Default fallback
    
    return {
        "route": route,
        "messages": [AIMessage(content=f"Supervisor decision: {route}")]
    }


def web_agent_node(state: AgentState) -> AgentState:
    """Web agent uses web_search_tool to answer query"""
    query = state["query"]
    
    # Call the tool
    result = web_search_tool(query)
    
    messages = [
        SystemMessage(content="You are a web research specialist. Use the search results to answer the query clearly."),
        HumanMessage(content=f"Query: {query}\n\nSearch Results: {result}\n\nProvide a clear answer.")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "agent_output": response.content,
        "messages": [AIMessage(content=f"Web Agent: {response.content}")]
    }


def rag_agent_node(state: AgentState) -> AgentState:
    """RAG agent uses rag_search_tool to answer query"""
    query = state["query"]
    
    # Call the tool
    result = rag_search_tool(query)
    
    messages = [
        SystemMessage(content="You are a knowledge base specialist. Use the internal docs to answer the query clearly."),
        HumanMessage(content=f"Query: {query}\n\nKnowledge Base Results: {result}\n\nProvide a clear answer.")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "agent_output": response.content,
        "messages": [AIMessage(content=f"RAG Agent: {response.content}")]
    }


def db_agent_node(state: AgentState) -> AgentState:
    """DB agent uses db_call_tool to answer query"""
    query = state["query"]
    
    # Call the tool
    result = db_call_tool(query)
    
    messages = [
        SystemMessage(content="You are a database specialist. Use the query results to answer clearly."),
        HumanMessage(content=f"Query: {query}\n\nDatabase Results: {result}\n\nProvide a clear answer.")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "agent_output": response.content,
        "messages": [AIMessage(content=f"DB Agent: {response.content}")]
    }


def final_answer_node(state: AgentState) -> AgentState:
    """
    Supervisor frames the final answer using:
    - Original query
    - Chosen route
    - Agent's output
    """
    query = state["query"]
    route = state["route"]
    agent_output = state["agent_output"]
    
    messages = [
        SystemMessage(content="You are a supervisor framing the final answer. Make it professional and clear."),
        HumanMessage(content=f"""Original Query: {query}

Chosen Route: {route}
Agent's Answer: {agent_output}

Frame a professional, clear final answer for the user.""")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "final_answer": response.content,
        "messages": [AIMessage(content=f"Final Answer: {response.content}")]
    }


# ========== ROUTING LOGIC ==========
def route_to_agent(state: AgentState) -> Literal["web_agent", "rag_agent", "db_agent"]:
    """
    Dynamic routing function - decides which agent node to execute next.
    This is the key difference from CrewAI - true dynamic routing!
    """
    route = state.get("route", "WEB")
    
    if route == "WEB":
        return "web_agent"
    elif route == "RAG":
        return "rag_agent"
    elif route == "DB":
        return "db_agent"
    else:
        return "web_agent"  # Default fallback


# ========== GRAPH CONSTRUCTION ==========
def create_graph():
    """Build the LangGraph state graph"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("web_agent", web_agent_node)
    workflow.add_node("rag_agent", rag_agent_node)
    workflow.add_node("db_agent", db_agent_node)
    workflow.add_node("final_answer", final_answer_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges (dynamic routing!)
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,  # This function decides which agent to call
        {
            "web_agent": "web_agent",
            "rag_agent": "rag_agent",
            "db_agent": "db_agent"
        }
    )
    
    # All agents go to final_answer node
    workflow.add_edge("web_agent", "final_answer")
    workflow.add_edge("rag_agent", "final_answer")
    workflow.add_edge("db_agent", "final_answer")
    
    # Final answer ends the graph
    workflow.add_edge("final_answer", END)
    
    return workflow.compile()


# ========== RUN FUNCTION ==========
def run(user_query: str) -> str:
    """
    Run the LangGraph workflow
    
    Flow:
    1. Supervisor node → decides route (WEB/RAG/DB)
    2. Dynamic routing → only chosen agent node executes
    3. Final answer node → supervisor frames the answer
    """
    graph = create_graph()
    
    # Initial state
    initial_state = {
        "messages": [],
        "query": user_query,
        "route": "",
        "agent_output": "",
        "final_answer": ""
    }
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    return result["final_answer"]


# ========== EXAMPLE USAGE ==========
if __name__ == "__main__":
    print("=" * 70)
    print("LangGraph Supervisor Pattern - Dynamic Routing")
    print("=" * 70)
    print("\nFlow:")
    print("1. Supervisor → decides WEB/RAG/DB")
    print("2. Dynamic routing → only chosen agent executes")
    print("3. Final answer → supervisor frames response")
    print("\n" + "=" * 70)
    
    # Example 1: Should route to WEB
    print("\nExample 1: General query (should route to WEB)")
    print("-" * 70)
    result1 = run("What are the latest AI trends in 2024?")
    print(f"\nFinal Answer:\n{result1}")
    
    # Example 2: Should route to RAG
    print("\n" + "=" * 70)
    print("\nExample 2: Company query (should route to RAG)")
    print("-" * 70)
    result2 = run("What is our company's remote work policy?")
    print(f"\nFinal Answer:\n{result2}")
    
    # Example 3: Should route to DB
    print("\n" + "=" * 70)
    print("\nExample 3: Database query (should route to DB)")
    print("-" * 70)
    result3 = run("What are the sales numbers for Q4 2024?")
    print(f"\nFinal Answer:\n{result3}")




#########################################################################################
## Example crew flow

"""
Supervisor Pattern - Single Crew Approach

Supervisor agent has access to all tools and:
1. Analyzes the user query
2. Decides which tool to use (web_search, rag_search, or db_call)
3. Uses that tool to answer the query
4. Provides a clear response

This is the simplest and most efficient approach!
"""

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# ========== TOOLS ==========

@tool("web_search_tool")
def web_search(query: str) -> str:
    """Simulated web search for public/latest info."""
    return f"[WEB SEARCH] Best public info about: {query}"


@tool("rag_tool")
def rag_search(query: str) -> str:
    """Simulated RAG over internal docs."""
    return f"[RAG] Internal knowledge for: {query}"


@tool("db_call_tool")
def db_call(query: str) -> str:
    """Simulated DB/API call for structured data."""
    return f"[DB] Queried database with: {query}"


# ========== CREW ORCHESTRATION ==========
def run(user_query: str) -> str:
    """
    Supervisor analyzes query, decides which tool to use, and answers.
    Supervisor has access to all tools and uses the appropriate one.
    """
    supervisor = Agent(
        role="Supervisor",
        goal="Read query, decide tool, and use it to answer.",
        backstory="You route and execute.",
        tools=[web_search, rag_search, db_call],  # Supervisor has all tools
        verbose=True,
    )
    
    task = Task(
        description=f"""
User query: "{user_query}"

1. Analyze the query and decide which tool is best:
   - web_search_tool → for public/latest info, general knowledge
   - rag_search_tool → for internal docs, company-specific knowledge
   - db_call_tool → for database queries, structured data

2. Use that tool to answer the query.

3. Provide a clear, helpful response based on the tool's results.
""",
        agent=supervisor,
        expected_output="Clear answer to the user's question.",
    )
    
    crew = Crew(
        agents=[supervisor],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew.kickoff()


if __name__ == "__main__":
    print("=" * 70)
    print("Supervisor Pattern: Single Crew with Tool Selection")
    print("=" * 70)
    result = run("What are the latest AI trends this year?")
    print("\n" + "=" * 70)
    print("FINAL RESULT:")
    print("=" * 70)
    print(result)
    
    print("\n" + "=" * 70)
    print("Example 2: Company-specific query (should use RAG)")
    print("=" * 70)
    result2 = run("What is our company's remote work policy?")
    print("\nFINAL RESULT:")
    print(result2)
