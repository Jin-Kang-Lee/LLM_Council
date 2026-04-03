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
from agents import RiskAgent, BusinessOpsRiskAgent, MasterAgent, GovernanceAgent
from config import API_HOST, API_PORT, MAX_DISCUSSION_ROUNDS
from rag.retriever import build_shared_reference_query, get_council_context, ensure_ingested
from rag.preprocessor import preprocess_context



# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print(" Multi-Agent Earnings Analyzer starting up...")
    print(f" Max discussion rounds: {MAX_DISCUSSION_ROUNDS}")
    await asyncio.to_thread(ensure_ingested)
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
        "parsed_data": parsed,
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
        "parsed_data": parsed,
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
            master_agent = MasterAgent()
            print("Agents initialized")

            parsed_data = session["parsed_data"]
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

            # Preprocessing: chunk ER, query RAG per chunk, merge into compact context
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 1.5,
                    "status": "preprocessing",
                    "message": "Preprocessing: chunking report and merging with accounting standards..."
                })
            }
            print("Preprocessing context...")
            compacted_content = await preprocess_context(parsed_data["cleaned_content"])
            print(f"Preprocessing complete. Compacted to {len(compacted_content)} chars.")


            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 1.5,
                    "status": "preprocessing_complete",
                    "message": f"Context compacted ({len(compacted_content)} chars). Starting analysis..."
                })
            }


            # Phase 2: Individual Analyses
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2,
                    "status": "started",
                    "message": "Starting individual agent analyses..."
                })
            }

            # Run risk analysis (uses compacted_content — no extra RAG retrieval needed)
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
                compacted_content,
                reference_context=None,
                reference_query=None,
                allow_targeted_retrieval=False,
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
                compacted_content,
                reference_context=None,
                reference_query=None,
                allow_targeted_retrieval=False,
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
                compacted_content,
                reference_context=None,
                reference_query=None,
                allow_targeted_retrieval=False,
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

            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2,
                    "status": "complete",
                    "message": "Individual analyses complete"
                })
            }

            # Phase 2.5: Position Papers — each agent stakes their ground before debate
            print("Generating war room position papers...")
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 2.5,
                    "status": "positions",
                    "message": "Agents preparing opening positions..."
                })
            }

            risk_position, business_ops_position, governance_position = await asyncio.gather(
                risk_agent.write_position_paper(risk_analysis),
                business_ops_agent.write_position_paper(business_ops_analysis),
                governance_agent.write_position_paper(governance_analysis),
            )

            position_papers = {
                "Risk Analyst":          risk_position,
                "Business & Ops Analyst": business_ops_position,
                "Governance Analyst":    governance_position,
            }

            # Phase 3: War Room Discussion
            yield {
                "event": "phase",
                "data": json.dumps({
                    "phase": 3,
                    "status": "started",
                    "message": "Agents entering the war room..."
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

                # Risk opens round 1 with the sharpest disagreement;
                # subsequent rounds must challenge the previous speaker on a specific point
                if round_num == 1:
                    risk_turn = (
                        "The war room is open. You go first — pick the sharpest disagreement "
                        "between the three positions and make your opening move. "
                        "Lead with a specific number or metric from the report."
                    )
                else:
                    gov_msg = next((m for m in reversed(discussion_messages) if m["agent"] == "Governance Analyst"), None)
                    risk_turn = risk_agent.respond_to(
                        "Governance Analyst",
                        gov_msg["content"] if gov_msg else discussion_messages[-1]["content"]
                    )

                risk_response = await risk_agent.generate_discussion(
                    position_papers, discussion_messages, risk_turn,
                    earnings_content=compacted_content
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

                # Business & Ops challenges Risk directly
                business_ops_response = await business_ops_agent.generate_discussion(
                    position_papers,
                    discussion_messages,
                    business_ops_agent.respond_to("Risk Analyst", risk_response),
                    earnings_content=compacted_content
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

                # Governance weighs in on both in round 1; in later rounds explicitly challenges
                # whichever of Risk or Business & Ops made the weakest governance argument
                if round_num == 1:
                    gov_turn = (
                        "Risk and Business & Ops have both weighed in. "
                        "What are they missing or getting wrong from a governance and compliance standpoint? "
                        "Be specific — name the exact claim you are pushing back on."
                    )
                else:
                    gov_turn = (
                        f"Risk just argued: '{risk_response[:400]}...'\n"
                        f"Business & Ops countered: '{business_ops_response[:400]}...'\n\n"
                        "Pick the argument you find most legally or regulatory problematic and challenge it. "
                        "Cite a specific compliance requirement or governance gap they are ignoring."
                    )

                gov_response = await governance_agent.generate_discussion(
                    position_papers, discussion_messages, gov_turn,
                    earnings_content=compacted_content
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
                "",
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
