"""
LangGraph Workflow Definition
Defines the multi-agent state machine for the earnings analysis pipeline.
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
import operator

from agents import RiskAgent, SentimentAgent, MasterAgent
from config import MAX_DISCUSSION_ROUNDS


class AgentMessage(TypedDict):
    """Structure for agent messages in discussion."""
    agent: str
    content: str
    round: int


class AnalysisState(TypedDict):
    """State managed throughout the analysis workflow."""
    # Input
    raw_content: str
    parsed_content: str
    
    # Phase 2: Individual Analyses
    risk_analysis: str
    sentiment_analysis: str
    
    # Phase 3: Discussion
    discussion_messages: Annotated[Sequence[AgentMessage], operator.add]
    discussion_round: int
    
    # Phase 4: Final Output
    final_report: str
    
    # Metadata
    current_phase: int
    status: str
    error: str


# Initialize agents
risk_agent = RiskAgent()
sentiment_agent = SentimentAgent()
master_agent = MasterAgent()


async def parse_node(state: AnalysisState) -> dict:
    """Phase 1: Content is already parsed before workflow starts."""
    return {
        "current_phase": 1,
        "status": "parsing_complete"
    }


async def risk_analysis_node(state: AnalysisState) -> dict:
    """Phase 2a: Run Risk Agent analysis."""
    try:
        analysis = await risk_agent.analyze(state["parsed_content"])
        return {
            "risk_analysis": analysis,
            "current_phase": 2,
            "status": "risk_analysis_complete"
        }
    except Exception as e:
        return {
            "risk_analysis": f"Error in risk analysis: {str(e)}",
            "error": str(e)
        }


async def sentiment_analysis_node(state: AnalysisState) -> dict:
    """Phase 2b: Run Sentiment Agent analysis."""
    try:
        analysis = await sentiment_agent.analyze(state["parsed_content"])
        return {
            "sentiment_analysis": analysis,
            "current_phase": 2,
            "status": "sentiment_analysis_complete"
        }
    except Exception as e:
        return {
            "sentiment_analysis": f"Error in sentiment analysis: {str(e)}",
            "error": str(e)
        }


async def discussion_node(state: AnalysisState) -> dict:
    """Phase 3: Agents discuss their findings."""
    current_round = state.get("discussion_round", 0) + 1
    messages = list(state.get("discussion_messages", []))
    
    try:
        if current_round == 1:
            # Risk agent starts by responding to sentiment analysis
            discussion_prompt = risk_agent.respond_to(
                "Sentiment Analyst",
                state["sentiment_analysis"],
                state["parsed_content"]
            )
            risk_response = await risk_agent.generate(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })
            
            # Sentiment agent responds
            discussion_prompt = sentiment_agent.respond_to(
                "Risk Analyst",
                risk_response,
                state["parsed_content"]
            )
            sentiment_response = await sentiment_agent.generate(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Sentiment Analyst",
                "content": sentiment_response,
                "round": current_round
            })
        else:
            # Subsequent rounds - agents respond to each other's last message
            last_sentiment = next(
                (m["content"] for m in reversed(messages) if m["agent"] == "Sentiment Analyst"),
                ""
            )
            last_risk = next(
                (m["content"] for m in reversed(messages) if m["agent"] == "Risk Analyst"),
                ""
            )
            
            # Risk responds to sentiment
            discussion_prompt = risk_agent.respond_to(
                "Sentiment Analyst",
                last_sentiment,
                state["parsed_content"]
            )
            risk_response = await risk_agent.generate(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })
            
            # Sentiment responds to risk
            discussion_prompt = sentiment_agent.respond_to(
                "Risk Analyst",
                risk_response,
                state["parsed_content"]
            )
            sentiment_response = await sentiment_agent.generate(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Sentiment Analyst",
                "content": sentiment_response,
                "round": current_round
            })
        
        return {
            "discussion_messages": messages,
            "discussion_round": current_round,
            "current_phase": 3,
            "status": f"discussion_round_{current_round}_complete"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "discussion_error"
        }


def should_continue_discussion(state: AnalysisState) -> Literal["discussion", "consolidation"]:
    """Determine if discussion should continue or move to consolidation."""
    current_round = state.get("discussion_round", 0)
    if current_round < MAX_DISCUSSION_ROUNDS:
        return "discussion"
    return "consolidation"


async def consolidation_node(state: AnalysisState) -> dict:
    """Phase 4: Master Agent consolidates all analyses."""
    try:
        # Format discussion transcript
        discussion_transcript = "\n\n".join([
            f"**{msg['agent']} (Round {msg['round']}):**\n{msg['content']}"
            for msg in state.get("discussion_messages", [])
        ])
        
        final_report = await master_agent.consolidate(
            state["parsed_content"],
            state["risk_analysis"],
            state["sentiment_analysis"],
            discussion_transcript
        )
        
        return {
            "final_report": final_report,
            "current_phase": 4,
            "status": "complete"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "consolidation_error"
        }


def create_workflow() -> StateGraph:
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AnalysisState)
    
    # Add nodes - names must not match state attribute names
    workflow.add_node("parse", parse_node)
    workflow.add_node("run_risk", risk_analysis_node)
    workflow.add_node("run_sentiment", sentiment_analysis_node)
    workflow.add_node("run_discussion", discussion_node)
    workflow.add_node("run_consolidation", consolidation_node)
    
    # Define edges
    workflow.set_entry_point("parse")
    
    # After parsing, run both analyses in parallel
    workflow.add_edge("parse", "run_risk")
    workflow.add_edge("parse", "run_sentiment")
    
    # Both analyses lead to discussion
    workflow.add_edge("run_risk", "run_discussion")
    workflow.add_edge("run_sentiment", "run_discussion")
    
    # Discussion can loop or proceed to consolidation
    workflow.add_conditional_edges(
        "run_discussion",
        should_continue_discussion,
        {
            "discussion": "run_discussion",
            "consolidation": "run_consolidation"
        }
    )
    
    # Consolidation ends the workflow
    workflow.add_edge("run_consolidation", END)
    
    return workflow.compile()


# Create the compiled workflow
analysis_workflow = create_workflow()
