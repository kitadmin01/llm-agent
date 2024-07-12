import unittest
from dynamodb_agent import DynamoDBAgent
from postgres_agent import PostgresAgent
from s3_agent import S3Agent
from unittest.mock import MagicMock

class TestAgents(unittest.TestCase):
    def setUp(self):
        self.dynamo_agent = DynamoDBAgent('OrdersTable')
        self.postgres_agent = PostgresAgent('postgresql://user:password@host:port/dbname')
        self.s3_agent = S3Agent('documents-bucket')

    def test_dynamodb_agent(self):
        self.dynamo_agent.table.get_item = MagicMock(return_value={'Item': {'order_id': '123'}})
        result = self.dynamo_agent.get_order_details('123')
        self.assertEqual(result['order_id'], '123')

    def test_postgres_agent(self):
        self.postgres_agent.conn.cursor = MagicMock()
        cursor = self.postgres_agent.conn.cursor.return_value.__enter__.return_value
        cursor.fetchall = MagicMock(return_value=[('transformer', 'details')])
        result = self.postgres_agent.get_additional_context('code123')
        self.assertEqual(result[0][0], 'transformer')

    def test_s3_agent(self):
        self.s3_agent.s3.list_objects_v2 = MagicMock(return_value={'Contents': [{'Key': 'doc1'}]})
        result = self.s3_agent.search_documents('code123')
        self.assertEqual(result[0], 'doc1')

if __name__ == '__main__':
    unittest.main()
