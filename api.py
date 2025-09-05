import os
import json
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

# Connect to Redis using the URL from your Render environment variable
redis_client = redis.from_url(os.environ.get("REDIS_URL"))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    image_url = data.get('image_url')
    webhook_url = data.get('webhook_url')

    if not image_url or not webhook_url:
        return jsonify({"error": "Missing image_url or webhook_url"}), 400

    # Create a job payload and push it to the queue
    job_payload = {
        'image_url': image_url,
        'webhook_url': webhook_url
    }
    redis_client.lpush('detection_jobs', json.dumps(job_payload))

    return jsonify({"message": "Job received and added to queue", "status": "processing"}), 202

if __name__ == '__main__':
    # Use 0.0.0.0 for Render deployment
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
