# 🤖 B3 & Crypto Autonomous Agent API

An enterprise-grade, event-streaming Backend API built for an Autonomous Financial Agent targeting the Brazilian market. 

This system uses **LangGraph** for multi-agent reasoning and tool-calling, and **FastAPI** to serve the agent's thought process in real-time (via Server-Sent Events).

## 🏗 Architecture (The Golden Stack)
- **Agentic Logic:** LangGraph (ReAct architecture)
- **LLM Engine:** OpenAI (`gpt-4o-mini`)
- **Backend Framework:** FastAPI (Async)
- **Streaming:** SSE (Server-Sent Events) for token-by-token streaming
- **Authentication:** Clerk Auth Middleware (Prepared)
- **Tools Included:** Mercado Bitcoin API (BRL Pricing), Brazilian Crypto Tax Calculator

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone <https://github.com/Kialojer?tab=repositories>
   cd crypto-ai-agent