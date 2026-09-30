# Technical Documentation: Optum Strategic Alpha Platform

## 1. Project Objective
Optum Strategic Alpha is a **Full-Stack Agentic Intelligence Platform** built to synchronize clinical breakthroughs with business strategy. It transforms raw medical data into high-fidelity "Strategic Alpha" reports through an orchestrated team of AI agents.

## 2. Platform Architecture

### A. The "Modern Enterprise" Dash (Frontend)
*   **Technology**: Vite + React + Vanilla CSS.
*   **Design**: High-end dark mode using glassmorphism and subtle micro-animations for agent "pulsing."
*   **Real-time Streaming**: Uses Server-Sent Events (SSE) to bridge the gap between the Python logic and the browser, allowing for a live "Chain of Thought" display.

### B. The Command Center (Backend API)
*   **Technology**: FastAPI + Uvicorn.
*   **Orchestration**: Manages mission lifecycle (Pending -> Running -> Completed/Failed) and captures stdout to stream live agent logs.

### C. The Intelligence Core (CrewAI & ResilientLLM)
*   **Framework**: CrewAI with a **Sequential Process** — 6-task, 5-agent pipeline.
*   **The "Autonomous Switch"**: Agents use a reasoning loop to decide between **Broad Search** (Serper/Tavily) and **Deep Extraction** (Scraper).
*   **5-Stream Swarm**:
    - **Healthcare Researcher** (Groq 8B): Ground-truth clinical facts.
    - **OptumHealth Strategist** (Mistral Large): Value-Based Care impact.
    - **OptumInsight Analyst** (Groq 70B): DaaS & AI workflow opportunities.
    - **OptumRx Specialist** (Ollama 120B): Pharmacy spend & formulary strategy.
    - **Financial Analyst** (Groq 70B): ROI, MLR delta, capital recommendation.
*   **Adaptive Brain Architecture**:
    - **Failover Logic**: Uses a custom `resilient_call` factory that monitors for 429/503 errors and autonomously pivots between Groq, Mistral, and Ollama Cloud.
    - **Preferred Strategy Stack**: High-IQ reasoning routed to Llama 3.3 70B (Groq) or Mistral Large, with Ollama 120B for specialty synthesis.

### D. The Clean Signal Shield (The Content Shield)
To ensure reports are executive-ready, the platform uses a **Stateless Content Shield**:
*   **Proxy Layer**: Every agent response is wrapped in a `CleanResponseProxy`.
*   **JSON Sanitization**: Technical metadata, token usage logs, and object wrappers are surgically stripped, delivering pure markdown to the final persistence layer.

## 3. Technology Stack Summary
- **Backend API**: FastAPI
- **Frontend**: React (Vite)
- **Agent Framework**: CrewAI + Litellm
- **Swarm Size**: 5 Agents / 6 Tasks
- **Failover Architecture**: Multi-Provider (Groq, Mistral, Ollama)
- **Search Toolset**: Serper.dev, Tavily AI, Native Scraper, DuckDuckGo
- **Report Structure**: 7-section executive brief (Clinical → Care → Tech → Pharmacy → Financial → Recommendation)
- **Persistence**: Automated Markdown reporting with metadata sanitization to `./reports`

---
*Created by Antigravity for Optum Strategy Teams.*
