from flask import Flask, request, jsonify
from dynamodb_agent import DynamoDBAgent
from postgres_agent import PostgresAgent
from s3_agent import S3Agent
from question_parser import QuestionParser
from response_aggregator import ResponseAggregator

app = Flask(__name__)

dynamo_agent = DynamoDBAgent('OrdersTable')
postgres_agent = PostgresAgent('postgresql://user:password@host:port/dbname')
s3_agent = S3Agent('documents-bucket')
question_parser = QuestionParser()
response_aggregator = ResponseAggregator(dynamo_agent, postgres_agent, s3_agent)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')
    question_type, params = question_parser.parse_question(question)
    if question_type:
        response = response_aggregator.aggregate_response(question_type, params)
        return jsonify(response)
    else:
        return jsonify({'error': 'Invalid question'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
