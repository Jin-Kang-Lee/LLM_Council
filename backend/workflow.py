"""
LangGraph Workflow Definition
Defines the multi-agent state machine for the earnings analysis pipeline.
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
import operator

from agents import RiskAgent, BusinessOpsRiskAgent, MasterAgent, GovernanceAgent, DeepResearchAgent
from rag.retriever import build_shared_reference_query, get_council_context
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

    # Shared RAG context
    reference_query: str
    reference_context: str

    # Phase 2: Individual Analyses
    risk_analysis: str
    business_ops_analysis: str
    governance_analysis: str
    research_analysis: str      # LLM-planned queries (pending JSON)
    research_results: str       # Enriched JSON after DDGS execution

    # Phase 2 → 3 bridge: Position papers (plain-language stances, not JSON)
    risk_position: str
    business_ops_position: str
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
business_ops_agent = BusinessOpsRiskAgent()
governance_agent = GovernanceAgent()
deep_research_agent = DeepResearchAgent()
master_agent = MasterAgent()


async def parse_node(state: AnalysisState) -> dict:
    """Phase 1: Content is already parsed before workflow starts."""
    return {
        "current_phase": 1,
        "status": "parsing_complete"
    }


async def reference_node(state: AnalysisState) -> dict:
    """Phase 1.5: Shared reference lookup for hybrid RAG."""
    try:
        query = build_shared_reference_query(state["parsed_content"])
        context = get_council_context(query) if query else ""
        return {
            "reference_query": query,
            "reference_context": context,
            "current_phase": 1,
            "status": "reference_context_ready",
        }
    except Exception as e:
        return {
            "reference_query": "",
            "reference_context": "",
            "error": str(e),
            "status": "reference_context_error",
        }


async def risk_analysis_node(state: AnalysisState) -> dict:
    """Phase 2a: Risk Agent analyses the report."""
    try:
        analysis = await risk_agent.analyze(
            state["parsed_content"],
            reference_context=state.get("reference_context", ""),
            reference_query=state.get("reference_query", ""),
            allow_targeted_retrieval=True,
        )
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


async def business_ops_analysis_node(state: AnalysisState) -> dict:
    """Phase 2b: Business & Ops Risk Agent analysis."""
    try:
        analysis = await business_ops_agent.analyze(
            state["parsed_content"],
            reference_context=state.get("reference_context", ""),
            reference_query=state.get("reference_query", ""),
            allow_targeted_retrieval=True,
        )
        return {
            "business_ops_analysis": analysis,
            "current_phase": 2,
            "status": "business_ops_analysis_complete"
        }
    except Exception as e:
        return {
            "business_ops_analysis": f"Error in business ops analysis: {str(e)}",
            "error": str(e)
        }


async def governance_analysis_node(state: AnalysisState) -> dict:
    """Phase 2c: Governance Agent analyses the report."""
    try:
        analysis = await governance_agent.analyze(
            state["parsed_content"],
            reference_context=state.get("reference_context", ""),
            reference_query=state.get("reference_query", ""),
            allow_targeted_retrieval=True,
        )
        return {
            "governance_analysis": analysis,
            "current_phase": 2,
            "status": "governance_analysis_complete"
        }
    except Exception as e:
        return {
            "governance_analysis": f"Error in governance analysis: {str(e)}",
            "error": str(e)
        }


async def research_node(state: AnalysisState) -> dict:
    """Phase 2.5a: Deep Research Agent plans the search queries."""
    try:
        analysis = await deep_research_agent.analyze(
            state["parsed_content"],
            reference_context=state.get("reference_context", ""),
            reference_query=state.get("reference_query", ""),
            allow_targeted_retrieval=True,
        )
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

    Each agent responds to the previous agent's output, building a threaded discussion.
    """
    current_round = state.get("discussion_round", 0) + 1
    thread = list(state.get("discussion_messages", []))

    try:
        if current_round == 1:
            # Risk opens by responding to business ops analysis
            discussion_prompt = risk_agent.respond_to(
                "Business & Ops Analyst",
                state.get("business_ops_analysis", ""),
            )
            risk_response = await risk_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })

            # Business & Ops responds to Risk
            discussion_prompt = business_ops_agent.respond_to(
                "Risk Analyst",
                risk_response,
            )
            business_ops_response = await business_ops_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Business & Ops Analyst",
                "content": business_ops_response,
                "round": current_round
            })

            # Governance responds to both
            discussion_prompt = governance_agent.respond_to(
                "Risk and Business & Ops Analysts",
                f"Risk says: {risk_response}\n\nBusiness & Ops says: {business_ops_response}",
            )
            governance_response = await governance_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Governance Analyst",
                "content": governance_response,
                "round": current_round
            })

        else:
            # Subsequent rounds — each agent builds on the previous
            last_msg = thread[-1]["content"]
            last_agent = thread[-1]["agent"]

            # Risk responds to whoever went last
            discussion_prompt = risk_agent.respond_to(last_agent, last_msg)
            risk_response = await risk_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })

            # Business & Ops responds to Risk
            discussion_prompt = business_ops_agent.respond_to("Risk Analyst", risk_response)
            business_ops_response = await business_ops_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Business & Ops Analyst",
                "content": business_ops_response,
                "round": current_round
            })

            # Governance responds to Business & Ops
            discussion_prompt = governance_agent.respond_to(
                "Business & Ops Analyst",
                business_ops_response,
            )
            governance_response = await governance_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            thread.append({
                "agent": "Governance Analyst",
                "content": governance_response,
                "round": current_round
            })

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
            state["business_ops_analysis"],
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

    # Add nodes
    workflow.add_node("parse",             parse_node)
    workflow.add_node("run_reference",     reference_node)
    workflow.add_node("run_risk",          risk_analysis_node)
    workflow.add_node("run_business_ops",  business_ops_analysis_node)
    workflow.add_node("run_governance",    governance_analysis_node)
    workflow.add_node("run_research",      research_node)
    workflow.add_node("execute_research",  execute_research_node)
    workflow.add_node("run_discussion",    discussion_node)
    workflow.add_node("run_consolidation", consolidation_node)

    workflow.set_entry_point("parse")

    # After parsing, run shared reference lookup
    workflow.add_edge("parse", "run_reference")

    # After reference lookup, run all analyses in parallel
    workflow.add_edge("run_reference", "run_risk")
    workflow.add_edge("run_reference", "run_business_ops")
    workflow.add_edge("run_reference", "run_governance")

    # All analyses feed into research planning
    workflow.add_edge("run_risk",         "run_research")
    workflow.add_edge("run_business_ops", "run_research")
    workflow.add_edge("run_governance",   "run_research")

    # Research planning → DDGS execution → discussion
    workflow.add_edge("run_research",    "execute_research")
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
