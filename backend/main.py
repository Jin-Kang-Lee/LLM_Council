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
from agents import RiskAgent, SentimentAgent, MasterAgent
from config import API_HOST, API_PORT, MAX_DISCUSSION_ROUNDS


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
        "agents": ["RiskAgent", "SentimentAgent", "MasterAgent"]
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
            # Initialize agents
            print(f"Initializing agents for session {session_id}...")
            risk_agent = RiskAgent()
            sentiment_agent = SentimentAgent()
            master_agent = MasterAgent()
            print("Agents initialized")

            parsed_content = session["parsed_content"]

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

            risk_analysis = await risk_agent.analyze(parsed_content)
            print("Risk Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "risk",
                    "status": "complete",
                    "content": risk_analysis
                })
            }

            # Run sentiment analysis
            print("Sentiment Agent starting analysis...")
            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "sentiment",
                    "status": "thinking",
                    "message": "Sentiment Analyst is analyzing..."
                })
            }

            sentiment_analysis = await sentiment_agent.analyze(parsed_content)
            print("Sentiment Agent analysis complete")

            yield {
                "event": "agent",
                "data": json.dumps({
                    "agent": "sentiment",
                    "status": "complete",
                    "content": sentiment_analysis
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
                        "Sentiment Analyst",
                        sentiment_analysis,
                        parsed_content
                    )
                else:
                    last_sentiment = discussion_messages[-1]["content"]
                    discussion_prompt = risk_agent.respond_to(
                        "Sentiment Analyst",
                        last_sentiment,
                        parsed_content
                    )

                risk_response = await risk_agent.generate(parsed_content, discussion_prompt)
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

                # Sentiment agent responds
                discussion_prompt = sentiment_agent.respond_to(
                    "Risk Analyst",
                    risk_response,
                    parsed_content
                )

                sentiment_response = await sentiment_agent.generate(parsed_content, discussion_prompt)
                discussion_messages.append({
                    "agent": "Sentiment Analyst",
                    "content": sentiment_response,
                    "round": round_num
                })

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "agent": "sentiment",
                        "agentName": "Sentiment Analyst",
                        "content": sentiment_response,
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
                sentiment_analysis,
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
            # Clean up session
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
