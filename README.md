# LLM Council: Multi-Agent Earnings Analyzer

An advanced financial analysis platform that leverages a "council" of specialized AI agents to dissect earnings reports. Built with **FastAPI**, **LangGraph**, and **Ollama**, it provides a transparent, multi-perspective view of corporate performance.

---

## Key Features

- **Multi-Agent Collaboration**: Features specialized agents (**Risk Analyst**, **Sentiment Analyst**, and **Master Analyst**) that collaborate to provide exhaustive insights.
- **Dynamic Agent Discussion**: Watch real-time "thinking" and back-and-forth debate between agents as they refine their findings.
- **Real-Time Streaming**: Powered by Server-Sent Events (SSE) for a seamless, live analysis experience.
- **Dual Input Modes**: Supports direct text input or PDF document uploads for earnings reports.
- **Local LLM Integration**: Uses **Ollama** for privacy-preserving, local model inference (defaulting to `qwen2.5:7b-instruct`).
- **Modern UI**: A premium, responsive interface built with React, Vite, and Tailwind CSS.

---

## Architecture & Workflow

The analysis follows a strict 5-Phase Workflow managed by LangGraph:

1.  **Phase 1: Parsing**: Extracting and structuring content from raw text or PDFs.
2.  **Phase 2: Individual Analysis**: Risk and Sentiment agents perform their specialized assessments independently.
3.  **Phase 3: Council Discussion**: Agents enter a multi-round debate, challenging and refining each other's viewpoints.
4.  **Phase 4: Consolidation**: The Master Analyst synthesizes the raw report, individual analyses, and the discussion transcript into a final "Executive Summary."
5.  **Phase 5: Delivery**: Real-time delivery of the final consolidated report.

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Orchestration**: LangChain & LangGraph
- **Streaming**: SSE (Server-Sent Events) via `sse-starlette`
- **Model Interface**: Ollama (Local LLM Support)
- **PDF Processing**: PyPDF2

### Frontend
- **Framework**: React (Vite)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Content Rendering**: React Markdown

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
pip install -r requirements.txt
python main.py
```

#### Option B: Conda Package Manager
```bash
cd backend
conda create -n llm_council python=3.9
conda activate llm_council
pip install -r requirements.txt
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

---

## Project Structure

```text
LLM_Council/
├── backend/                # FastAPI Server
│   ├── agents/             # Specialized AI Agent logic
│   ├── main.py             # API Entry point
│   ├── workflow.py         # LangGraph orchestration
│   └── document_parser.py  # PDF/Text processing
├── frontend/               # React Project
│   ├── src/
│   │   ├── components/     # UI Components
│   │   └── App.jsx         # Main application logic
│   └── tailwind.config.js  # Styling configuration
└── README.md
```

---

## Configuration

You can adjust backend settings in `backend/config.py`:
- `OLLAMA_MODEL`: Choose your preferred local model.
- `MAX_DISCUSSION_ROUNDS`: Control how many times agents debate.
- `API_PORT`: Customize the server port.

---

## License

This project is open-source and available under the MIT License.
