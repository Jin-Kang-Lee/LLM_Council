# LLM Council: Multi-Agent Earnings Analyzer

An advanced financial analysis platform that leverages a **"council"** of specialized AI agents to dissect corporate earnings reports. Built with **FastAPI**, **LangGraph**, and **Ollama**, it provides a transparent, multi-perspective view of corporate performance through structured debate, RAG-grounded analysis, and real-time tool calling.

---

## Key Features

- **Multi-Agent Council**: Four specialized agents (**Risk Analyst**, **Business & Ops Analyst**, **Governance Analyst**, and **Master Analyst**) collaborate to deliver exhaustive, multi-domain insights.
- **War Room Debate**: Agents engage in structured, multi-round adversarial debate — each agent challenges the others' claims, cites report evidence, and surfaces blindspots before a final consolidation.
- **Retrieval-Augmented Generation (RAG)**: A hybrid RAG pipeline backed by **ChromaDB** and **Sentence Transformers** grounds agent analyses in a curated reference library of accounting standards (ASC 606/842/326) and sector benchmarks (Damodaran, Federal Reserve).
- **Real-Time Tool Calling**: Agents can invoke live financial tools (powered by **yfinance**) to fetch real-time company financials, insider trading data, and competitor benchmarking during analysis.
- **Real-Time Streaming**: Server-Sent Events (SSE) power a seamless, live analysis experience in the browser — watch agents think, debate, and consolidate in real time.
- **Dual Input Modes**: Supports direct text input or PDF document uploads. PDFs are parsed via **LlamaCloud** (with local **PyPDF2** fallback).
- **Comprehensive Evaluation Suite**: A full offline evaluation pipeline (`start_test.py`) with 8 automated metrics — schema integrity, reference-based accuracy, section completeness, War Room quality (LLM-as-Judge via GPT-4o), query diversity, RAG retrieval, RAG faithfulness, and output variance.
- **Modern UI**: A premium, responsive interface built with React, Vite, and Tailwind CSS.

---

## Architecture & Workflow

The analysis follows a strict **Multi-Phase Workflow** managed by LangGraph:

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Phase 1    │     │  Phase 1.5       │     │  Phase 2            │
│  Parsing    │────▶│  RAG Reference   │────▶│  Individual         │
│             │     │  Lookup          │     │  Analysis (×3)      │
└─────────────┘     └──────────────────┘     └─────────┬───────────┘
                                                       │
                         ┌─────────────────────────────▼───────────────┐
                         │  Phase 2.5 — Position Papers                │
                         │  Each agent writes 3 sharp opening claims   │
                         └─────────────────────────────┬───────────────┘
                                                       │
                         ┌─────────────────────────────▼───────────────┐
                         │  Phase 3 — War Room Discussion              │
                         │  Multi-round adversarial debate              │
                         │  (Risk → Business & Ops → Governance ×N)    │
                         └─────────────────────────────┬───────────────┘
                                                       │
                         ┌─────────────────────────────▼───────────────┐
                         │  Phase 4 — Consolidation                    │
                         │  Master Analyst synthesizes final report     │
                         └─────────────────────────────┬───────────────┘
                                                       │
                         ┌─────────────────────────────▼───────────────┐
                         │  Phase 5 — Delivery                         │
                         │  Real-time SSE delivery of JSON report      │
                         └─────────────────────────────────────────────┘
```

1. **Phase 1 — Parsing**: Extract and structure content from raw text or PDFs (LlamaCloud or PyPDF2). Post-processing cleans headers/footers, dehyphenates, and normalizes tables.
2. **Phase 1.5 — RAG Reference Lookup**: Build a shared reference query from the parsed report and retrieve relevant accounting standards and benchmarks from ChromaDB.
3. **Phase 2 — Individual Analysis**: Each specialist agent performs a multi-stage analysis pipeline:
   - **Stage 1**: Extract raw observations (no RAG).
   - **Stage 2**: Query the reference library for each observation.
   - **Stage 3**: Ground observations against retrieved RAG chunks.
   - **Stage 4**: Synthesize grounded conclusions into structured JSON.
4. **Phase 2.5 — Position Papers**: Each agent distills their analysis into 3 sharp, evidence-backed claims as opening positions for debate.
5. **Phase 3 — War Room**: Multi-round adversarial debate. Risk opens, Business & Ops challenges, Governance weighs in. Each agent must cite report evidence and challenge prior claims — no echo chamber.
6. **Phase 4 — Consolidation**: The Master Analyst synthesizes all analyses and the full discussion transcript into a final structured investment report (JSON).
7. **Phase 5 — Delivery**: Real-time SSE streaming of all phases to the frontend.

---

## Specialized Agents

| Agent | Role | Tools | Output Format |
|---|---|---|---|
| **Risk Analyst** | Financial risk — liquidity, leverage, debt, credit risk | `get_company_financials` (yfinance) | JSON with risk ratings, key risk factors, watchlist |
| **Business & Ops Analyst** | Operational risk — CapEx, margins, supply chain, pricing power | `get_competitor_benchmarking` (yfinance) | JSON with operational risk rating, business risks, non-disclosures |
| **Governance Analyst** | Governance & compliance — board structure, audit quality, legal risk | `get_insider_trading` (yfinance) | JSON with governance/compliance risk levels, key findings |
| **Master Analyst** | Synthesis — resolves disagreements, delivers final recommendation | — | JSON executive summary with recommendation |

---

## Technology Stack

### Backend
| Component | Technology |
|---|---|
| **Framework** | FastAPI + Uvicorn |
| **LLM Orchestration** | LangChain, LangGraph |
| **Streaming** | SSE via `sse-starlette` |
| **Model Interface** | Ollama (local LLM — default: `qwen2.5:7b-instruct-q2_K`) |
| **RAG Vector Store** | ChromaDB |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Reranker** | Cross-encoder (`ms-marco-MiniLM-L-6-v2`) |
| **PDF Parsing** | LlamaCloud (API) / PyPDF2 (local fallback) |
| **Live Financial Data** | yfinance |
| **Evaluation Judges** | OpenAI GPT-4o (War Room), Ollama (RAG faithfulness) |

### Frontend
| Component | Technology |
|---|---|
| **Framework** | React 18 (Vite) |
| **Styling** | Tailwind CSS |
| **Icons** | Lucide React |
| **Markdown Rendering** | React Markdown |

---

## Getting Started

### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- **Ollama**: [Download and install Ollama](https://ollama.com/)

### 1. Setup Ollama
Ensure Ollama is running and pull the required model:
```bash
ollama pull qwen2.5:7b-instruct-q2_K
```

### 2. Backend Setup

You can choose between using a standard Python Virtual Environment or Conda.

#### Option A: Python Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements.txt
python main.py
```

#### Option B: Conda Package Manager
```bash
cd backend
conda create -n llm_council python=3.9
conda activate llm_council
pip install -r ../requirements.txt
python main.py
```
*The backend will start on `http://localhost:8000`*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*The frontend will start on `http://localhost:5173`*

### 4. Environment Variables (Optional)

Create a `.env` file in the `backend/` directory for optional features:

```env
# LlamaCloud API key — enables high-quality PDF parsing (optional)
LLAMA_CLOUD_API_KEY=your_key_here

# OpenAI API key — enables War Room LLM-as-Judge evaluation (optional)
OPENAI_API_KEY=sk-...

# RAG tuning (all optional — sensible defaults are built in)
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
RAG_MAX_CHUNKS=4
RAG_FETCH_K=12
```

---

## Project Structure

```
LLM_Council/
├── backend/                        # FastAPI Server
│   ├── main.py                     # API entry point & SSE streaming
│   ├── config.py                   # All configuration (Ollama, RAG, API)
│   ├── workflow.py                 # LangGraph state machine orchestration
│   ├── document_parser.py          # PDF/text parsing (LlamaCloud + PyPDF2)
│   ├── md_postprocess.py           # Markdown cleanup (headers, tables, wraps)
│   ├── agents/                     # Specialized AI agents
│   │   ├── base_agent.py           # Abstract base — tool calling, RAG, retry
│   │   ├── risk_agent.py           # Financial Risk Analyst
│   │   ├── business_ops_agent.py   # Business & Ops Risk Analyst
│   │   ├── governance_agent.py     # Governance & Compliance Analyst
│   │   ├── master_agent.py         # Master Analyst (synthesis)
│   │   └── sentiment_agent.py      # (Legacy) Sentiment Analyst
│   ├── tools/                      # Agent tool definitions
│   │   └── finance_tools.py        # yfinance wrappers + tool registry
│   ├── rag/                        # RAG pipeline
│   │   ├── ingest.py               # Markdown → ChromaDB ingestion
│   │   ├── retriever.py            # Semantic search + rerank
│   │   ├── reranker.py             # Cross-encoder reranking
│   │   ├── guardrails.py           # Query sanitization & chunk filtering
│   │   └── query.py                # CLI helper for manual RAG queries
│   ├── eval/                       # Evaluation framework
│   │   ├── pipeline.py             # Core evaluation orchestrator
│   │   ├── capture_warroom.py      # War Room capture for offline judging
│   │   ├── master_agent_eval.py    # Master Agent benchmark (CoT/few-shot)
│   │   ├── generate_barcharts.py   # Matplotlib bar chart visualisation
│   │   ├── generate_heatmap.py     # Matplotlib heatmap visualisation
│   │   ├── generate_judge_prompts.py # Generate judge prompt .txt files
│   │   ├── warroom_judge_eval.ipynb # Jupyter notebook for judge eval
│   │   ├── metrics/                # Evaluation metrics
│   │   │   ├── schema_integrity.py
│   │   │   ├── reference_based.py
│   │   │   ├── section_check.py
│   │   │   ├── warroom_judge.py    # GPT-4o LLM-as-Judge (bias-mitigated)
│   │   │   ├── query_diversity.py
│   │   │   ├── rag_retrieval.py
│   │   │   └── rag_faithfulness_llm.py
│   │   ├── test_data/              # Test case JSON files
│   │   ├── judge_prompts/          # Generated judge prompt .txt files
│   │   ├── war_room_results/       # Captured war room transcripts
│   │   └── master_agent_eval/      # Master Agent eval data & results
│   ├── data/
│   │   └── reference_library/      # RAG source documents
│   │       ├── PWC_ASC606.md       # Revenue recognition guidance
│   │       ├── EY_ASC842.md        # Lease accounting guidance
│   │       ├── EY_ASC326.md        # Credit loss (CECL) guidance
│   │       ├── Damodaran_Credit_Rating.md
│   │       ├── Damodaran_Debt_Sector_Fundamentals.md
│   │       ├── Damodraran_Sector_Margins.md
│   │       └── FedReserve_Macro.md
│   └── start_test.py               # CLI entry point for evaluation
├── frontend/                       # React + Vite Frontend
│   ├── src/
│   │   ├── App.jsx                 # Main application logic
│   │   ├── main.jsx                # React entry point
│   │   ├── index.css               # Global styles
│   │   └── components/
│   │       ├── UploadZone.jsx      # File/text input
│   │       ├── PhaseIndicator.jsx  # Workflow phase progress
│   │       ├── AgentCards.jsx      # Agent analysis display
│   │       ├── DiscussionLog.jsx   # War Room chat view
│   │       ├── FinalReport.jsx     # Consolidated report display
│   │       ├── Header.jsx          # App header
│   │       └── DeepResearchSpace.jsx
│   ├── index.html                  # HTML entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── data/
│   └── mock_report.md              # Sample earnings report for testing
├── requirements.txt                # Root-level Python dependencies
└── README.md
```

---

## Evaluation Pipeline

Run the full evaluation suite from the `backend/` directory:

```bash
# Run all tests
python start_test.py --input="eval/test_data/test_data.json" --tests=all

# Run specific tests
python start_test.py --input="eval/test_data/test_data.json" --tests=schema,reference

# Run with War Room judge (requires OpenAI key)
python start_test.py --input="eval/test_data/test_data.json" --tests=warroom --openai_key=sk-...

# Run a specific test case
python start_test.py --input="eval/test_data/test_data.json" --tests=all --case=TC-001 --verbose
```

### Available Evaluation Metrics

| Metric | Description |
|---|---|
| `schema` | Validates agent JSON outputs against expected schemas |
| `reference` | Compares outputs against ground-truth values (categorical + F1) |
| `section` | Checks Master Agent report contains all required sections |
| `warroom` | GPT-4o judges War Room quality on 5 dimensions (bias-mitigated) |
| `diversity` | Measures diversity of RAG queries across agents |
| `rag` | Evaluates RAG retrieval quality against expected sources |
| `rag_faithfulness` | LLM-judged faithfulness of evidence to retrieved context |
| `variance` | Output consistency across multiple runs |

---

## Configuration

Adjust backend settings in `backend/config.py`:

| Setting | Description | Default |
|---|---|---|
| `OLLAMA_MODEL` | Local LLM model for analysis | `qwen2.5:7b-instruct-q2_K` |
| `MAX_DISCUSSION_ROUNDS` | War Room debate rounds | `3` |
| `API_PORT` | Backend server port | `8000` |
| `RAG_EMBEDDING_MODEL` | Sentence Transformer model | `all-MiniLM-L6-v2` |
| `RAG_RERANK_MODEL` | Cross-encoder reranker | `ms-marco-MiniLM-L-6-v2` |
| `RAG_MAX_CHUNKS` | Max retrieved chunks | `4` |
| `RAG_FETCH_K` | Initial retrieval pool size | `12` |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Detailed health (Ollama status, active agents) |
| `POST` | `/analyze/text` | Start text-based analysis → returns session ID |
| `POST` | `/analyze/pdf` | Start PDF-based analysis → returns session ID |
| `GET` | `/analyze/stream/{session_id}` | SSE stream of analysis phases |
| `GET` | `/sessions` | List active analysis sessions |

---
