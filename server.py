import os
import json
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent import app as agent_graph


load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
app = FastAPI(
    title="Crypto BRL Arbitrage API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)


class ChatRequest(BaseModel):
    question: str
    thread_id: str

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard)
):
    user_id = creds.decoded["sub"]
    print(f"👤 User {user_id} connected")

    initial_state = {
        "messages": [HumanMessage(content=request.question)]
    }


    config = {"configurable": {"thread_id": user_id}}

    async def event_stream():

       
         async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as memory:
            await memory.setup()

            
            graph = agent_graph.with_config({
                "checkpointer": memory
            }) # type: ignore

            
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v2"
            ):

                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content

                    if chunk:
                        yield f"data: {json.dumps({'text': chunk})}\n\n"

            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":

    uvicorn.run(app)