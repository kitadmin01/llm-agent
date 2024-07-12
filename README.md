# AI Multi-Agent Utility Application

This repository contains the implementation of an AI multi-agent application for a utility company. The application assists technicians in identifying and understanding electric outages before traveling to customer locations. Technicians interact with a chatbot to gather necessary information, which helps them prepare with the required tools and resources.

## Overview

The application uses multiple agents to fetch and aggregate data from various sources:
- **DynamoDB**: Retrieves current electric outage orders.
- **Postgres**: Searches historical customer data.
- **S3**: Searches for documents containing device characteristics (e.g., transformers, switches).

A supervisor agent decides the workflow based on the responses from these agents. The final response is generated using AWS Bedrock models.

## Workflow

1. The user's request is first processed by the **DynamoDB agent** to get more details about the current order.
2. The **Supervisor agent** then decides whether to:
    - Use the **Postgres agent** to get customer data.
    - Use the **S3 agent** to get characteristics of any device.
    - Or generate the final response if enough information is available.
3. The **Response agent** generates the final answer using the AWS Bedrock model.
4. The workflow includes an **END** node to signify the termination of the process.

## Prerequisites

- Python 3.7+
- AWS SDK for Python (Boto3)
- psycopg2 library for PostgreSQL
- Langgraph Core libraries

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/kitadmin01/llm-agent.git
    cd ai-multi-agent-utility
    ```

2. Install the required Python packages:
    ```bash
    pip install boto3 psycopg2
    ```

## Configuration

Ensure your AWS credentials and configurations are properly set up. This includes access to DynamoDB, S3, and AWS Bedrock services.

## Running the Application

1. Define your agents and their respective configurations in the `agents.py` file.
2. Run the `agents.py` script:
    ```bash
    python agents.py
    ```

## Example Usage

The example usage in the script demonstrates how to send a user request and process the workflow:
```python
if __name__ == "__main__":
    initial_state = {"messages": [HumanMessage(content="Find customers that have the same transformer type T123")]}
    for state in graph.stream(initial_state):
        print(state)
        print("----")
