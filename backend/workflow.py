"""
LangGraph Workflow Definition
Defines the multi-agent state machine for the earnings analysis pipeline.
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
import operator

from agents import RiskAgent, SentimentAgent, MasterAgent, GovernanceAgent, DeepResearchAgent
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

    # Phase 2: Individual Analyses (full JSON)
    risk_analysis: str
    sentiment_analysis: str
    governance_analysis: str
    research_analysis: str      # LLM-planned queries (pending JSON)
    research_results: str       # Enriched JSON after DDGS execution

    # Phase 2 → 3 bridge: Position papers (plain-language stances, not JSON)
    risk_position: str
    sentiment_position: str
    governance_position: str

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
governance_agent = GovernanceAgent()
deep_research_agent = DeepResearchAgent()
master_agent = MasterAgent()


async def parse_node(state: AnalysisState) -> dict:
    """Phase 1: Content is already parsed before workflow starts."""
    return {
        "current_phase": 1,
        "status": "parsing_complete"
    }


async def risk_analysis_node(state: AnalysisState) -> dict:
    """Phase 2a: Risk Agent analyses the report, then writes its position paper."""
    try:
        analysis = await risk_agent.analyze(state["parsed_content"])
        position = await risk_agent.write_position_paper(analysis)
        return {
            "risk_analysis": analysis,
            "risk_position": position,
            "current_phase": 2,
            "status": "risk_analysis_complete"
        }
    except Exception as e:
        return {
            "risk_analysis": f"Error in risk analysis: {str(e)}",
            "risk_position": "",
            "error": str(e)
        }


async def sentiment_analysis_node(state: AnalysisState) -> dict:
    """Phase 2b: Sentiment Agent analyses the report, then writes its position paper."""
    try:
        analysis = await sentiment_agent.analyze(state["parsed_content"])
        position = await sentiment_agent.write_position_paper(analysis)
        return {
            "sentiment_analysis": analysis,
            "sentiment_position": position,
            "current_phase": 2,
            "status": "sentiment_analysis_complete"
        }
    except Exception as e:
        return {
            "sentiment_analysis": f"Error in sentiment analysis: {str(e)}",
            "sentiment_position": "",
            "error": str(e)
        }


async def governance_analysis_node(state: AnalysisState) -> dict:
    """Phase 2c: Governance Agent analyses the report, then writes its position paper."""
    try:
        analysis = await governance_agent.analyze(state["parsed_content"])
        position = await governance_agent.write_position_paper(analysis)
        return {
            "governance_analysis": analysis,
            "governance_position": position,
            "current_phase": 2,
            "status": "governance_analysis_complete"
        }
    except Exception as e:
        return {
            "governance_analysis": f"Error in governance analysis: {str(e)}",
            "governance_position": "",
            "error": str(e)
        }


async def research_node(state: AnalysisState) -> dict:
    """Phase 2.5a: Deep Research Agent plans the search queries."""
    try:
        analysis = await deep_research_agent.analyze(state["parsed_content"])
        return {
            "research_analysis": analysis,
            "current_phase": 2,
            "status": "research_plan_complete"
        }
    except Exception as e:
        return {
            "research_analysis": f"Error in research planning: {str(e)}",
            "error": str(e)
        }


async def execute_research_node(state: AnalysisState) -> dict:
    """Phase 2.5b: Execute planned queries via DDGS and store results in state."""
    try:
        enriched = await deep_research_agent.execute_searches(state["research_analysis"])
        return {
            "research_results": enriched,
            "current_phase": 2,
            "status": "research_execution_complete"
        }
    except Exception as e:
        return {
            "research_results": state.get("research_analysis", ""),
            "error": str(e)
        }


async def discussion_node(state: AnalysisState) -> dict:
    """
    Phase 3: War room debate.

    Each agent gets:
      - system:  their persona (not the report)
      - user:    DDGS research findings (if any)
      - user:    all 3 position papers
      - user/assistant: full conversation thread so far
      - user:    their specific turn instruction

    The full report is NOT re-sent here — agents already extracted
    what matters into their JSON analyses and position papers.
    """
    current_round = state.get("discussion_round", 0) + 1
    thread = list(state.get("discussion_messages", []))

    position_papers = {
        "Risk Analyst":       state.get("risk_position", ""),
        "Sentiment Analyst":  state.get("sentiment_position", ""),
        "Governance Analyst": state.get("governance_position", ""),
    }
    research = state.get("research_results", "")

    try:
        if current_round == 1:
            # Risk opens — no prior thread, picks the sharpest disagreement between positions
            risk_response = await risk_agent.generate_discussion(
                position_papers,
                [],
                "The war room is open. You go first — pick the sharpest disagreement "
                "between the three positions and make your opening move.",
                research,
            )
            thread.append({"agent": "Risk Analyst", "content": risk_response, "round": current_round})

            # Sentiment responds to Risk's opening
            sentiment_response = await sentiment_agent.generate_discussion(
                position_papers,
                thread,
                risk_agent.respond_to("Risk Analyst", risk_response),
                research,
            )
            thread.append({"agent": "Sentiment Analyst", "content": sentiment_response, "round": current_round})

            # Governance weighs in on both
            governance_response = await governance_agent.generate_discussion(
                position_papers,
                thread,
                "Risk and Sentiment have both weighed in. What are they missing or getting "
                "wrong from a governance and compliance standpoint?",
                research,
            )
            thread.append({"agent": "Governance Analyst", "content": governance_response, "round": current_round})

        else:
            # Subsequent rounds — full thread is in messages, each agent builds on it
            last_msg    = thread[-1]["content"]
            last_agent  = thread[-1]["agent"]

            risk_response = await risk_agent.generate_discussion(
                position_papers,
                thread,
                risk_agent.respond_to(last_agent, last_msg),
                research,
            )
            thread.append({"agent": "Risk Analyst", "content": risk_response, "round": current_round})

            sentiment_response = await sentiment_agent.generate_discussion(
                position_papers,
                thread,
                sentiment_agent.respond_to("Risk Analyst", risk_response),
                research,
            )
            thread.append({"agent": "Sentiment Analyst", "content": sentiment_response, "round": current_round})

            governance_response = await governance_agent.generate_discussion(
                position_papers,
                thread,
                governance_agent.respond_to("Sentiment Analyst", sentiment_response),
                research,
            )
            thread.append({"agent": "Governance Analyst", "content": governance_response, "round": current_round})

        return {
            "discussion_messages": thread,
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
    if state.get("discussion_round", 0) < MAX_DISCUSSION_ROUNDS:
        return "discussion"
    return "consolidation"


async def consolidation_node(state: AnalysisState) -> dict:
    """Phase 4: Master Agent consolidates all analyses."""
    try:
        discussion_transcript = "\n\n".join([
            f"**{msg['agent']} (Round {msg['round']}):**\n{msg['content']}"
            for msg in state.get("discussion_messages", [])
        ])

        research = state.get("research_results") or state.get("research_analysis", "")

        final_report = await master_agent.consolidate(
            state["parsed_content"],
            state["risk_analysis"],
            state["sentiment_analysis"],
            state["governance_analysis"],
            research,
            discussion_transcript,
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

    workflow.add_node("parse",              parse_node)
    workflow.add_node("run_risk",           risk_analysis_node)
    workflow.add_node("run_sentiment",      sentiment_analysis_node)
    workflow.add_node("run_governance",     governance_analysis_node)
    workflow.add_node("run_research",       research_node)
    workflow.add_node("execute_research",   execute_research_node)
    workflow.add_node("run_discussion",     discussion_node)
    workflow.add_node("run_consolidation",  consolidation_node)

    workflow.set_entry_point("parse")

    # Parallel analyses after parse
    workflow.add_edge("parse", "run_risk")
    workflow.add_edge("parse", "run_sentiment")
    workflow.add_edge("parse", "run_governance")

    # All analyses feed into research planning
    workflow.add_edge("run_risk",       "run_research")
    workflow.add_edge("run_sentiment",  "run_research")
    workflow.add_edge("run_governance", "run_research")

    # Research planning → DDGS execution → discussion
    workflow.add_edge("run_research",     "execute_research")
    workflow.add_edge("execute_research", "run_discussion")

    workflow.add_conditional_edges(
        "run_discussion",
        should_continue_discussion,
        {
            "discussion":    "run_discussion",
            "consolidation": "run_consolidation"
        }
    )

    workflow.add_edge("run_consolidation", END)

    return workflow.compile()


# Create the compiled workflow
analysis_workflow = create_workflow()
