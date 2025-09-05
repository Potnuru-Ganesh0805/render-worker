import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import redis

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Connect to the Redis instance using the URL provided by Render
try:
    redis_client = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
    redis_client = None

@app.route('/predict', methods=['POST'])
def predict():
    if redis_client is None:
        return jsonify({"error": "Redis connection failed. Cannot add job to queue."}), 503

    data = request.get_json()
    image_url = data.get('image_url')
    webhook_url = data.get('webhook_url')

    if not image_url or not webhook_url:
        return jsonify({"error": "Missing 'image_url' or 'webhook_url' in request body"}), 400

    job_payload = {
        'image_url': image_url,
        'webhook_url': webhook_url
    }
    redis_client.lpush('detection_jobs', json.dumps(job_payload))

    return jsonify({"message": "Job received and queued", "status": "processing"}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
