"""
LangGraph Workflow Definition
Defines the multi-agent state machine for the earnings analysis pipeline.
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
import operator

from agents import RiskAgent, BusinessOpsRiskAgent, MasterAgent, GovernanceAgent, DeepResearchAgent
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
    business_ops_analysis: str
    governance_analysis: str
    research_analysis: str
    
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


async def business_ops_analysis_node(state: AnalysisState) -> dict:
    """Phase 2b: Run Business & Ops Risk Agent analysis."""
    try:
        analysis = await business_ops_agent.analyze(state["parsed_content"])
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
    """Phase 2c: Run Governance Agent analysis."""
    try:
        analysis = await governance_agent.analyze(state["parsed_content"])
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
    """Phase 2.5: Deep Research into gaps identified in analyses."""
    try:
        analysis = await deep_research_agent.analyze(state["parsed_content"])
        return {
            "research_analysis": analysis,
            "current_phase": 2,
            "status": "research_complete"
        }
    except Exception as e:
        return {
            "research_analysis": f"Error in research: {str(e)}",
            "error": str(e)
        }


async def discussion_node(state: AnalysisState) -> dict:
    """Phase 3: Agents discuss their findings."""
    current_round = state.get("discussion_round", 0) + 1
    messages = list(state.get("discussion_messages", []))
    
    try:
        if current_round == 1:
            # Risk agent starts by responding to business ops analysis
            discussion_prompt = risk_agent.respond_to(
                "Business & Ops Analyst",
                state["business_ops_analysis"],
                state["parsed_content"]
            )
            risk_response = await risk_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })
            
            # Business & Ops agent responds to Risk
            discussion_prompt = business_ops_agent.respond_to(
                "Risk Analyst",
                risk_response,
                state["parsed_content"]
            )
            business_ops_response = await business_ops_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Business & Ops Analyst",
                "content": business_ops_response,
                "round": current_round
            })

            # Governance agent responds to both
            discussion_prompt = governance_agent.respond_to(
                "Risk and Business & Ops Analysts",
                f"Risk says: {risk_response}\n\nBusiness & Ops says: {business_ops_response}",
                state["parsed_content"]
            )
            gov_response = await governance_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Governance Analyst",
                "content": gov_response,
                "round": current_round
            })
        else:
            # Subsequent rounds - agents respond to the previous chain
            last_msg = messages[-1]["content"]
            last_agent = messages[-1]["agent"]
            
            # 1. Risk responds to whoever went last (Governance)
            discussion_prompt = risk_agent.respond_to(
                last_agent,
                last_msg,
                state["parsed_content"]
            )
            risk_response = await risk_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Risk Analyst",
                "content": risk_response,
                "round": current_round
            })
            
            # 2. Business & Ops responds to Risk
            discussion_prompt = business_ops_agent.respond_to(
                "Risk Analyst",
                risk_response,
                state["parsed_content"]
            )
            business_ops_response = await business_ops_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Business & Ops Analyst",
                "content": business_ops_response,
                "round": current_round
            })

            # 3. Governance responds to Business & Ops
            discussion_prompt = governance_agent.respond_to(
                "Business & Ops Analyst",
                business_ops_response,
                state["parsed_content"]
            )
            gov_response = await governance_agent.generate_discussion(
                state["parsed_content"],
                discussion_prompt
            )
            messages.append({
                "agent": "Governance Analyst",
                "content": gov_response,
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
            state["business_ops_analysis"],
            state["governance_analysis"],
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
    workflow.add_node("run_business_ops", business_ops_analysis_node)
    workflow.add_node("run_governance", governance_analysis_node)
    workflow.add_node("run_research", research_node)
    workflow.add_node("run_discussion", discussion_node)
    workflow.add_node("run_consolidation", consolidation_node)
    
    # Define edges
    workflow.set_entry_point("parse")
    
    # After parsing, run all analyses in parallel
    workflow.add_edge("parse", "run_risk")
    workflow.add_edge("parse", "run_business_ops")
    workflow.add_edge("parse", "run_governance")
    
    # All analyses lead to research
    workflow.add_edge("run_risk", "run_research")
    workflow.add_edge("run_business_ops", "run_research")
    workflow.add_edge("run_governance", "run_research")
    
    # Research leads to discussion
    workflow.add_edge("run_research", "run_discussion")
    
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
