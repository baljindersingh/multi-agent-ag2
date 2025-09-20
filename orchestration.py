from autogen import ConversableAgent
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import AutoPattern
from typing import Any

import os
import random

# Configure Ollama endpoint (local LLM)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Shared config for agents
llm_config = {
    "api_type": "ollama",
    "model": "phi3",  # requires 'ollama pull phi3'
    "base_url": OLLAMA_BASE_URL,
    "temperature": 0.2,
}

# Define the system message for our finance bot
finance_system_message = """
You are a financial compliance assistant. You will be given a set of transaction descriptions.
For each transaction:
- If it seems suspicious (e.g., amount > $10,000, vendor is unusual, memo is vague), ask the human agent for approval.
- Otherwise, approve it automatically.
Provide the full set of transactions to approve at one time.
If the human gives a general approval, it applies to all transactions requiring approval.
When all transactions are processed, summarize the results and say "You can type exit to finish".
"""

# Define the system message for the summary agent
summary_system_message = """
You are a financial summary assistant. You will be given a set of transaction details and their approval status.
Your task is to summarize the results of the transactions processed by the finance bot.
Generate a markdown table with the following columns:
- Vendor
- Memo
- Amount
- Status (Approved/Rejected)
The summary should include the total number of transactions, the number of approved transactions, and the number of rejected transactions.
The summary should be concise and clear.

Once you generated the summary append the below in the summary:
==== SUMMARY GENERATED ====
"""

# Create the finance agent with LLM intelligence
finance_bot = ConversableAgent(
    name="finance_bot",
    llm_config=llm_config,
    system_message=finance_system_message,
)

# Create the summary agent to generate formatted transaction reports
summary_bot = ConversableAgent(
    name="summary_bot",
    llm_config=llm_config,
    system_message=summary_system_message,
)

def is_termination_msg(x: dict[str, Any]) -> bool:
    content = x.get("content", "")
    return (content is not None) and "==== SUMMARY GENERATED ====" in content

# Create the human agent for oversight
human = ConversableAgent(
    name="human",
    human_input_mode="ALWAYS",  # Always ask for human input
)

# Generate sample transactions - this creates different transactions each time you run
VENDORS = ["Staples", "Acme Corp", "CyberSins Ltd", "Initech", "Globex", "Unicorn LLC"]
MEMOS = ["Quarterly supplies", "Confidential", "NDA services", "Routine payment", "Urgent request", "Reimbursement"]

def generate_transaction():
    amount = random.choice([500, 1500, 9999, 12000, 23000, 4000])
    vendor = random.choice(VENDORS)
    memo = random.choice(MEMOS)
    return f"Transaction: ${amount} to {vendor}. Memo: {memo}."

# Generate 3 random transactions
transactions = [generate_transaction() for _ in range(3)]

# Format the initial message
initial_prompt = (
    "Please process the following transactions one at a time:\n\n" +
    "\n".join([f"{i+1}. {tx}" for i, tx in enumerate(transactions)])
)

# Create pattern and start group chat
pattern = AutoPattern(
    initial_agent=finance_bot,
    agents=[finance_bot, summary_bot],
    user_agent=human,
    group_manager_args = {
        "llm_config": llm_config,
        "is_termination_msg": is_termination_msg
    },
)

result, _, _ = initiate_group_chat(
    pattern=pattern,
    messages=initial_prompt,
)