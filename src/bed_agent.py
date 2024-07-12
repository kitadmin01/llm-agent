import re
import boto3
import psycopg2
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, AgentState, END  # Import END

# Define DynamoDB Agent
class DynamoDBAgent:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def get_order_details(self, order_id):
        response = self.table.get_item(Key={'order_id': order_id})
        return response.get('Item', None)

# Define Postgres Search Agent
class PostgresAgent:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
    
    def get_additional_context(self, transformer_code):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM transformers WHERE code = %s", (transformer_code,))
            return cursor.fetchall()

# Define S3 Document Search Agent
class S3Agent:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def search_documents(self, transformer_code):
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=f"transformers/{transformer_code}")
        documents = response.get('Contents', [])
        return [doc['Key'] for doc in documents]

    def get_document(self, document_key):
        response = self.s3.get_object(Bucket=self.bucket_name, Key=document_key)
        return response['Body'].read()

# Define Question Parsing Engine
class QuestionParser:
    def parse_question(self, question):
        patterns = {
            'transformer_code': r'Find .* transformer code (\w+)',
            'fuse_type': r'Find .* fuse type (\w+)',
            'surge_protectors': r'Find .* Surge protectors',
            'power_poles_lines': r'Find .* Power poles and lines',
            'outlets_switches': r'Find .* Outlets and switches type',
            'outage_type': r'Find .* outage type'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, question)
            if match:
                return key, match.groups()
        return None, None

# Define Response Aggregator
class ResponseAggregator:
    def __init__(self):
        self.responses = {}

    def add_response(self, agent_name, response):
        self.responses[agent_name] = response

    def get_combined_context(self):
        return " ".join([str(self.responses.get(agent, "")) for agent in self.responses])

# Initialize AWS Bedrock client
bedrock_client = boto3.client('bedrock-runtime')

# Create a function to generate responses using AWS Bedrock models
def generate_response(question, context):
    response = bedrock_client.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        inputText=question + " " + context
    )
    return response['generatedText']

# Create agents
dynamo_agent = DynamoDBAgent('OrdersTable')
postgres_agent = PostgresAgent('postgresql://user:password@host:port/dbname')
s3_agent = S3Agent('documents-bucket')
question_parser = QuestionParser()
response_aggregator = ResponseAggregator()

# Define the Langgraph nodes
def dynamo_node(state):
    message = state["messages"][-1].content
    question_type, params = question_parser.parse_question(message)
    if question_type:
        transformer_code = params[0]
        order_details = dynamo_agent.get_order_details(transformer_code)
        response_aggregator.add_response("DynamoDB", order_details)
    return state

def postgres_node(state):
    message = state["messages"][-1].content
    question_type, params = question_parser.parse_question(message)
    if question_type:
        transformer_code = params[0]
        context = postgres_agent.get_additional_context(transformer_code)
        response_aggregator.add_response("Postgres", context)
    return state

def s3_node(state):
    message = state["messages"][-1].content
    question_type, params = question_parser.parse_question(message)
    if question_type:
        transformer_code = params[0]
        documents = s3_agent.search_documents(transformer_code)
        response_aggregator.add_response("S3", documents)
    return state

def response_node(state):
    message = state["messages"][-1].content
    combined_context = response_aggregator.get_combined_context()
    response = generate_response(message, combined_context)
    return {
        "messages": [HumanMessage(content=response, sender="ResponseAgent")],
        "sender": "ResponseAgent",
    }

def supervisor_node(state):
    # Supervisor logic to decide the next step based on the response so far
    combined_context = response_aggregator.get_combined_context()
    if "transformer" in combined_context:
        next_step = "S3Agent"
    elif "customer data" in combined_context:
        next_step = "PostgresAgent"
    else:
        next_step = "ResponseAgent"
    
    return next_step

# Define the Langgraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("DynamoDBAgent", dynamo_node)
workflow.add_node("PostgresAgent", postgres_node)
workflow.add_node("S3Agent", s3_node)
workflow.add_node("ResponseAgent", response_node)
workflow.add_node("SupervisorAgent", supervisor_node)
workflow.add_node(END, lambda state: state)  # Add END node

# Define conditional edges based on supervisor's decision
workflow.add_conditional_edges(
    "DynamoDBAgent",
    supervisor_node,
    {
        "PostgresAgent": "PostgresAgent",
        "S3Agent": "S3Agent",
        "ResponseAgent": "ResponseAgent",
        END: END,
    },
)

workflow.set_entry_point("DynamoDBAgent")
graph = workflow.compile()

# Example usage
if __name__ == "__main__":
    initial_state = {"messages": [HumanMessage(content="Find customers that have the same transformer type T123")]}
    for state in graph.stream(initial_state):
        print(state)
        print("----")
