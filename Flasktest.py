import unittest
import boto3
from moto import mock_s3, mock_dynamodb2
from io import BytesIO
from app import app, S3_BUCKET, DYNAMO_TABLE

class FlaskAppTestCase(unittest.TestCase):
    
    @mock_s3
    @mock_dynamodb2
    def setUp(self):
        self.client = app.test_client()
        
        # Create mock S3 bucket
        self.s3 = boto3.client("s3", region_name="us-east-2")
        self.s3.create_bucket(Bucket=S3_BUCKET)

        # Create mock DynamoDB table
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
        self.dynamodb.create_table(
            TableName=DYNAMO_TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
    
    @mock_s3
    @mock_dynamodb2
    def test_upload_image(self):
        data = {
            "file": (BytesIO(b"dummy data"), "test.jpg"),
            "user_id": "123",
            "description": "Test image"
        }
        response = self.client.post("/upload", content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("file_id", response.json)

    @mock_s3
    @mock_dynamodb2
    def test_list_images(self):
        response = self.client.get("/images")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    @mock_s3
    @mock_dynamodb2
    def test_view_image(self):
        image_id = "dummy-image-id"
        response = self.client.get(f"/image/{image_id}")
        self.assertIn(response.status_code, [200, 404])
    
    @mock_s3
    @mock_dynamodb2
    def test_delete_image(self):
        image_id = "dummy-image-id"
        response = self.client.delete(f"/delete/{image_id}")
        self.assertIn(response.status_code, [200, 404])

if __name__ == "__main__":
    unittest.main()
