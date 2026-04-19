import os
import uuid
import json
import requests
from typing import Annotated
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
load_dotenv(override=True)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


@tool
def get_crypto_price_brl(symbol: str) -> str:
    """
    Fetch current price of a cryptocurrency across 5 major Brazilian exchanges.
    Input: Symbol (e.g., 'BTC', 'ETH'). Returns JSON string.
    """
    symbol_upper = symbol.upper().strip()
    symbol_lower = symbol.lower().strip()
    results = []

    endpoints = [
        {"name": "Mercado Bitcoin", "url": f"https://api.mercadobitcoin.net/api/v4/tickers?symbols={symbol_upper}-BRL", "path": lambda r: float(r[0]['last'])},
        {"name": "Binance", "url": f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_upper}BRL", "path": lambda r: float(r["price"])},
        {"name": "NovaDAX", "url": f"https://api.novadax.com/v1/market/ticker?symbol={symbol_upper}_BRL", "path": lambda r: float(r['data']['lastPrice'])},
        {"name": "Brasil Bitcoin", "url": f"https://brasilbitcoin.com.br/API/prices/{symbol_upper}", "path": lambda r: float(r['last'])},
        {"name": "Bitso", "url": f"https://api.bitso.com/v3/ticker/?book={symbol_lower}_brl", "path": lambda r: float(r['payload']['last'])}
    ]

    for ep in endpoints:
        try:
            res = requests.get(ep["url"], timeout=5).json()
            price = ep["path"](res)
            results.append({"exchange": ep["name"], "price": price, "symbol": symbol_upper})
        except:
            results.append({"exchange": ep["name"], "error": "Not available"})

    return json.dumps(results)


llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
tools = [get_crypto_price_brl]
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools)



def Guardrail_node(state: AgentState):
    """ check  input whit Gardrail"""
    user_message = state["messages"][-1].content.lower()
    
   
    bad_words = ["sex", "fuck", "porn", "shit"]
    if any(word in user_message for word in bad_words):
        return {"messages": [AIMessage(content="🛡️ Security: Your question contains prohibited language.")]}
    

    compliance_prompt = f"""Analyze the user's request:
    1. Is it related to crypto/finance?
    2. Is it asking for illegal acts (tax evasion, laundering)?
    Respond ONLY: TOPIC:[YES/NO], LEGAL:[SAFE/UNSAFE]"""
    
    check = llm.invoke([HumanMessage(content=compliance_prompt + f"\nUser: {user_message}")]).content.upper()
    
    if "TOPIC: NO" in check:
        return {"messages": [AIMessage(content="I am a specialized Crypto AI. Please ask about crypto prices.")]}
    if "LEGAL: UNSAFE" in check:
        return {"messages": [AIMessage(content="🛡️ Legal: I cannot assist with illegal financial activities.")]}

    print("✅ Input Guardrail Passed.")
    return {}

def reasoning_agent_node(state: AgentState):
    """brain of agent"""
    sys_msg = SystemMessage(content="""You are an expert Crypto Arbitrage AI for Brazil.
    1. Use get_crypto_price_brl for coin prices.
    2. List all prices and point out the cheapest exchange.
    3. End with the RAW JSON in a ```json block.""")
    
    messages = [sys_msg] + state["messages"]
    print("🧠 Agent is thinking... this agent desing with Kiarash T.N")

    return {"messages": [llm_with_tools.invoke(messages)]}

def Output_Guardrail_node(state: AgentState):
    """ output Gardrail """
    last_msg = state["messages"][-1].content

    check_prompt = f"Review this for financial advice or broken JSON. If bad, fix it. Otherwise reply 'SAFE'. \nText: {last_msg}"
    
    review = llm.invoke([HumanMessage(content=check_prompt)]).content.upper()

    if "SAFE" not in review and len(review) > 10: 
        return {"messages": [AIMessage(content=review)]}
    
    print("✅ Output Guardrail Passed.")
    return {}


def route_after_guardrail(state: AgentState):
    if isinstance(state["messages"][-1], AIMessage):
        return END
    return "Agent"

def route_after_agent(state: AgentState):
    condition = tools_condition(state)
    if condition == "tools":
        return "tools"
    return "OutputGuardrail"


builder = StateGraph(AgentState)

builder.add_node("Guardrail", Guardrail_node)
builder.add_node("Agent", reasoning_agent_node)
builder.add_node("tools", tool_node)
builder.add_node("OutputGuardrail", Output_Guardrail_node)

builder.add_edge(START, "Guardrail")
builder.add_conditional_edges("Guardrail", route_after_guardrail)
builder.add_conditional_edges("Agent", route_after_agent)
builder.add_edge("tools", "Agent")
builder.add_edge("OutputGuardrail", END)

app = builder.compile(checkpointer=memory)


if __name__ == "__main__":
    test_id = str(uuid.uuid4())
    query = "What is the price of Solana (SOL) in Brazil?"
    
    inputs = {"messages": [HumanMessage(content=query)]}
    config = {"configurable": {"thread_id": test_id}}
    
    final_state = app.invoke(inputs, config=config)
    print("\n" + "="*50)
    print("🤖 Final Response:\n", final_state["messages"][-1].content)
    print("="*50)