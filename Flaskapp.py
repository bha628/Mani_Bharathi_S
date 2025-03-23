from flask import Flask, request, jsonify
from flask_lambda import FlaskLambda
import boto3
import uuid
import os
from botocore.exceptions import NoCredentialsError

app = FlaskLambda(__name__)

# AWS Configurations
S3_BUCKET = "your-s3-bucket-name"
DYNAMO_TABLE = "your-dynamo-table-name"
AWS_REGION = "your-region"

s3_client = boto3.client("s3")
dynamo_client = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamo_client.Table(DYNAMO_TABLE)

# Upload Image API
@app.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    metadata = request.form.to_dict()
    file_id = str(uuid.uuid4())
    file_name = file_id + os.path.splitext(file.filename)[-1]
    
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, file_name)
        metadata["id"] = file_id
        metadata["file_name"] = file_name
        table.put_item(Item=metadata)
        return jsonify({"message": "File uploaded successfully", "file_id": file_id}), 201
    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500

# List Images API with Filters
@app.route("/images", methods=["GET"])
def list_images():
    filter_key = request.args.get("filter_key")
    filter_value = request.args.get("filter_value")
    
    scan_kwargs = {}
    if filter_key and filter_value:
        scan_kwargs["FilterExpression"] = f"{filter_key} = :val"
        scan_kwargs["ExpressionAttributeValues"] = {":val": filter_value}
    
    response = table.scan(**scan_kwargs)
    return jsonify(response.get("Items", [])), 200

# View/Download Image API
@app.route("/image/<image_id>", methods=["GET"])
def view_image(image_id):
    response = table.get_item(Key={"id": image_id})
    if "Item" not in response:
        return jsonify({"error": "Image not found"}), 404
    
    file_name = response["Item"]["file_name"]
    url = s3_client.generate_presigned_url("get_object", Params={"Bucket": S3_BUCKET, "Key": file_name}, ExpiresIn=3600)
    return jsonify({"url": url}), 200

# Delete Image API
@app.route("/delete/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    response = table.get_item(Key={"id": image_id})
    if "Item" not in response:
        return jsonify({"error": "Image not found"}), 404
    
    file_name = response["Item"]["file_name"]
    s3_client.delete_object(Bucket=S3_BUCKET, Key=file_name)
    table.delete_item(Key={"id": image_id})
    return jsonify({"message": "Image deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)
