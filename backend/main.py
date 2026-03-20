"""
FastAPI Server - Main Entry Point
Provides REST API endpoints for the Multi-Agent Earnings Analyzer.
"""

import asyncio
import json
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from document_parser import parse_earnings_content, format_for_agents
from workflow import analysis_workflow, AnalysisState
from agents import RiskAgent, BusinessOpsRiskAgent, MasterAgent, GovernanceAgent, DeepResearchAgent
from config import API_HOST, API_PORT, MAX_DISCUSSION_ROUNDS
from rag.retriever import build_shared_reference_query, get_council_context


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print(" Multi-Agent Earnings Analyzer starting up...")
    print(f" Max discussion rounds: {MAX_DISCUSSION_ROUNDS}")
    yield
    print(" Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Earnings Analyzer",
    description="A 5-phase multi-agent system for analyzing financial earnings reports",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using "*" origins
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class TextAnalysisRequest(BaseModel):
    """Request model for text-based analysis."""
    content: str


class AnalysisResponse(BaseModel):
    """Response model for analysis status updates."""
    phase: int
    status: str
    data: Optional[dict] = None
    error: Optional[str] = None


# Store for active analysis sessions
active_sessions: dict = {}


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Multi-Agent Earnings Analyzer",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    import httpx

    ollama_status = "unknown"
    print("Checking Ollama status at http://localhost:11434/api/tags...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                ollama_status = "connected"
                print("Ollama status: connected")
            else:
                ollama_status = f"unhealthy ({response.status_code})"
                print(f"Ollama status: {ollama_status}")
    except Exception as e:
        ollama_status = f"disconnected: {str(e)}"
        print(f"Ollama status: {ollama_status}")

    return {
        "status": "healthy",
        "ollama": ollama_status,
        "agents": ["RiskAgent", "BusinessOpsRiskAgent", "GovernanceAgent", "MasterAgent"]
    }


@app.post("/analyze/text")
async def analyze_text(request: TextAnalysisRequest):
    """
    Start analysis of text content.
    Returns a session ID for streaming updates.
    """
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    # Parse the content
    parsed = await parse_earnings_content(request.content)
    formatted = format_for_agents(parsed)
    
    # Create session ID
    import uuid
    session_id = str(uuid.uuid4())
    
    # Store initial state
    active_sessions[session_id] = {
        "raw_content": request.content,
        "parsed_content": formatted,
        "status": "initialized",
        "phase": 0
    }
    
    return {
        "session_id": session_id,
        "parsed": parsed,
        "message": "Analysis initialized. Connect to /analyze/stream/{session_id} for updates."
    }


@app.post("/analyze/pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """
    Start analysis of PDF content.
    Returns a session ID for streaming updates.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    pdf_bytes = await file.read()
    
    # Parse the PDF
    parsed = await parse_earnings_content("", is_pdf=True, pdf_bytes=pdf_bytes)
    formatted = format_for_agents(parsed)
    
    # Create session ID
    import uuid
    session_id = str(uuid.uuid4())
    
    # Store initial state
    active_sessions[session_id] = {
        "raw_content": parsed["raw_content"],
        "parsed_content": formatted,
        "status": "initialized",
        "phase": 0
    }
    
    return {
        "session_id": session_id,
        "parsed": parsed,
        "message": "Analysis initialized. Connect to /analyze/stream/{session_id} for updates."
    }


@app.get("/analyze/stream/{session_id}")
async def stream_analysis(session_id: str):
    """
    Stream analysis updates via Server-Sent Events.
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    async def event_generator():
        """Generate SSE events for the analysis workflow."""
        import traceback
        try:
            print(f"Initializing agents for session {session_id}...")
            risk_agent = RiskAgent()
            business_ops_agent = BusinessOpsRiskAgent()
            governance_agent = GovernanceAgent()
            deep_research_agent = DeepResearchAgent()
            master_agent = MasterAgent()
            print("Agents initialized")

            parsed_content = session["parsed_content"]
            shared_reference_query = build_shared_reference_query(parsed_content)
            shared_reference_context = (
                get_council_context(shared_reference_query) if shared_reference_query else ""
            )

            # Phase 1: Parsing Complete
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 1,
                    "status": "complete",
                    "message": "Content parsed successfully"
                })
            }
            await asyncio.sleep(0.5)

            # Phase 2: Individual Analyses
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2,
                    "status": "started",
                    "message": "Starting individual agent analyses..."
                })
            }

            # Run risk analysis
            print("Risk Agent starting analysis...")
            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "risk",
                    "status": "thinking",
                    "message": "Risk Analyst is analyzing..."
                })
            }

            risk_analysis = await risk_agent.analyze(
                parsed_content,
                reference_context=shared_reference_context,
                reference_query=shared_reference_query,
                allow_targeted_retrieval=True,
            )
            print("Risk Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "risk",
                    "status": "complete",
                    "content": risk_analysis,
                    "reference_context": getattr(risk_agent, "last_reference_context", ""),
                    "reference_query": getattr(risk_agent, "last_reference_query", "")
                })
            }

            # Run business ops analysis
            print("Business & Ops Agent starting analysis...")
            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "business_ops",
                    "status": "thinking",
                    "message": "Business & Ops Analyst is analyzing..."
                })
            }

            business_ops_analysis = await business_ops_agent.analyze(
                parsed_content,
                reference_context=shared_reference_context,
                reference_query=shared_reference_query,
                allow_targeted_retrieval=True,
            )
            print("Business & Ops Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "business_ops",
                    "status": "complete",
                    "content": business_ops_analysis,
                    "reference_context": getattr(business_ops_agent, "last_reference_context", ""),
                    "reference_query": getattr(business_ops_agent, "last_reference_query", "")
                })
            }

            # Run governance analysis
            print("Governance Agent starting analysis...")
            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "governance",
                    "status": "thinking",
                    "message": "Governance Analyst is analyzing..."
                })
            }

            governance_analysis = await governance_agent.analyze(
                parsed_content,
                reference_context=shared_reference_context,
                reference_query=shared_reference_query,
                allow_targeted_retrieval=True,
            )
            print("Governance Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "governance",
                    "status": "complete",
                    "content": governance_analysis,
                    "reference_context": getattr(governance_agent, "last_reference_context", ""),
                    "reference_query": getattr(governance_agent, "last_reference_query", "")
                })
            }

            # Run deep research
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2.5,
                    "status": "started",
                    "message": "Analytic gaps identified. Initiating deep research..."
                })
            }

            print("Deep Research Agent starting analysis...")
            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "research",
                    "status": "thinking",
                    "message": "Deep Research Analyst is identifying gaps..."
                })
            }

            research_analysis = await deep_research_agent.analyze(
                parsed_content,
                reference_context=shared_reference_context,
                reference_query=shared_reference_query,
                allow_targeted_retrieval=True,
            )
            print("Deep Research Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "research",
                    "status": "complete",
                    "content": research_analysis,
                    "reference_context": getattr(deep_research_agent, "last_reference_context", ""),
                    "reference_query": getattr(deep_research_agent, "last_reference_query", "")
                })
            }

            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2,
                    "status": "complete",
                    "message": "Individual analyses complete"
                })
            }

            # Phase 3: Agent Discussion
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 3,
                    "status": "started",
                    "message": "Agents entering discussion phase..."
                })
            }

            discussion_messages = []

            for round_num in range(1, MAX_DISCUSSION_ROUNDS + 1):
                print(f"Discussion Round {round_num}/{MAX_DISCUSSION_ROUNDS} starting...")
                yield {
                    "event": "discussion",
                    "data": json.dumps({
                        "round": round_num,
                        "status": "started"
                    })
                }

                # Risk agent responds
                if round_num == 1:
                    discussion_prompt = risk_agent.respond_to(
                        "Business & Ops Analyst",
                        business_ops_analysis,
                        parsed_content
                    )
                else:
                    last_msg = discussion_messages[-1]["content"]
                    discussion_prompt = risk_agent.respond_to(
                        "Business & Ops Analyst",
                        last_msg,
                        parsed_content
                    )

                risk_response = await risk_agent.generate_discussion(
                    parsed_content,
                    discussion_prompt
                )
                discussion_messages.append({
                    "agent": "Risk Analyst",
                    "content": risk_response,
                    "round": round_num
                })

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "agent": "risk",
                        "agentName": "Risk Analyst",
                        "content": risk_response,
                        "round": round_num
                    })
                }

                # Business & Ops agent responds
                discussion_prompt = business_ops_agent.respond_to(
                    "Risk Analyst",
                    risk_response,
                    parsed_content
                )

                business_ops_response = await business_ops_agent.generate_discussion(
                    parsed_content,
                    discussion_prompt
                )
                discussion_messages.append({
                    "agent": "Business & Ops Analyst",
                    "content": business_ops_response,
                    "round": round_num
                })

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "agent": "business_ops",
                        "agentName": "Business & Ops Analyst",
                        "content": business_ops_response,
                        "round": round_num
                    })
                }

                # Governance agent responds
                discussion_prompt = governance_agent.respond_to(
                    "Risk and Business & Ops Analysts",
                    f"Risk says: {risk_response}\n\nBusiness & Ops says: {business_ops_response}",
                    parsed_content
                )

                gov_response = await governance_agent.generate_discussion(
                    parsed_content,
                    discussion_prompt
                )
                discussion_messages.append({
                    "agent": "Governance Analyst",
                    "content": gov_response,
                    "round": round_num
                })

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "agent": "governance",
                        "agentName": "Governance Analyst",
                        "content": gov_response,
                        "round": round_num
                    })
                }

                yield {
                    "event": "discussion",
                    "data": json.dumps({
                        "round": round_num,
                        "status": "complete"
                    })
                }

            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 3,
                    "status": "complete",
                    "message": "Discussion phase complete"
                })
            }

            # Phase 4: Consolidation
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 4,
                    "status": "started",
                    "message": "Master Analyst consolidating findings..."
                })
            }

            discussion_transcript = "\n\n".join([
                f"**{msg['agent']} (Round {msg['round']}):**\n{msg['content']}"
                for msg in discussion_messages
            ])

            print("Master Agent consolidating findings...")
            final_report = await master_agent.consolidate(
                parsed_content,
                risk_analysis,
                business_ops_analysis,
                governance_analysis,
                research_analysis,
                discussion_transcript
            )
            print("Final report generated")

            yield {
                "event": "report",
                "data": json.dumps({
                    "content": final_report
                })
            }

            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 4,
                    "status": "complete",
                    "message": "Analysis complete!"
                })
            }

            yield {
                "event": "complete",
                "data": json.dumps({
                    "message": "All phases complete",
                    "success": True
                })
            }
            print(f"Session {session_id} analysis complete!")
        except Exception as e:
            print("Error during analysis stream:")
            print(traceback.format_exc())
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "message": "Analysis failed"
                })
            }
        finally:
            if session_id in active_sessions:
                del active_sessions[session_id]

    return EventSourceResponse(event_generator())


@app.get("/sessions")
async def list_sessions():
    """List active analysis sessions."""
    return {
        "active_sessions": list(active_sessions.keys()),
        "count": len(active_sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
