# Optum Strategic Research Alpha 🏥

An AI-powered, multi-agent research system built with **CrewAI** and **Groq**, designed to generate institutional-grade strategic insights aligned with **Optum's three business pillars**.

---

## What it Does

Given a healthcare or pharmaceutical topic, this system deploys a **team of 5 specialized AI agents** that simultaneously analyze the topic through the three lenses of Optum's business model and synthesize a final "Strategic Alpha" report.

## Architecture

```
User Topic
    │
    ▼
┌─────────────────────────────┐
│   Healthcare Data Researcher │  ← Single Source of Truth (searches web)
└─────────────────────────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
 OptumHealth  OptumInsight  OptumRx   Financial
 Strategist   Analyst      Specialist  Analyst
 (VBC/Care)  (Data/AI/Ops) (PBM/Pharma) (ROI/MLR)
    │           │           │           │
    └───────────┴───────────┴───────────┘
                      │
                      ▼
              Strategic Synthesis
                      │
                      ▼
          Optum Strategic Alpha Report (.md)
```

## Agent Roles

| Agent | Optum Unit | Focus |
|---|---|---|
| Healthcare Data Researcher | Foundation | Clinical facts, FDA filings, breakthroughs |
| OptumHealth Strategist | OptumHealth | Value-Based Care, patient outcomes |
| OptumInsight Analyst | OptumInsight | AI workflows, Data-as-a-Service |
| OptumRx Specialist | OptumRx | Pharmacy spend, PBM, formulary |
| Financial Analyst | Cross-unit | ROI, MLR impact, investment thesis |

## Tech Stack

- **Framework**: CrewAI
- **LLM**: Llama 3.3 70B via Groq (with Mistral & Ollama failover)
- **Search Tools**: Serper (Google), Tavily AI, DuckDuckGo (fallback)
- **Resiliency**: Adaptive Brain — multi-provider failover on rate-limit errors

## Getting Started

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd Understand_Agents
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` and fill in your API keys:
```bash
cp .env.example .env
```

Required keys:
```
GROQ_API_KEY=gsk_...
SERPER_API_KEY=...       # Optional (Google Search)
TAVILY_API_KEY=...       # Optional (AI Search)
MISTRAL_API_KEY=...      # Optional (Failover LLM)
```

### 4. Run the crew
```bash
python research_crew.py
```
Enter a topic when prompted (e.g., `"GLP-1 Drugs in Obesity Management"`) and the crew will produce a full strategic report saved to `reports/`.

## Project Structure

```
Understand_Agents/
├── research_crew.py          # Main multi-agent engine
├── api.py                    # Optional REST API wrapper
├── requirements.txt          # Dependencies
├── .env.example              # API key template
├── .gitignore
├── architecture/
│   └── system_design.md      # System design & architecture diagram
├── TECHNICAL_DOCUMENTATION.md
└── reports/                  # Generated reports (git-ignored)
```

## Roadmap

- [ ] Manager/Orchestrator Agent (hierarchical process)
- [ ] Cross-session memory (vector DB persistence)
- [ ] Human-in-the-loop review checkpoint
- [ ] QA Agent for output scoring

---
*Built with CrewAI · Powered by Groq · Aligned with Optum's Strategic Priorities*
