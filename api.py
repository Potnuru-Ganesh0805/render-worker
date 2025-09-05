import os
import json
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

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

    # Create a job payload and push it to the queue
    job_payload = {
        'image_url': image_url,
        'webhook_url': webhook_url
    }
    # lpush is used to add the job to the left side of the queue
    redis_client.lpush('detection_jobs', json.dumps(job_payload))

    return jsonify({"message": "Job received and queued", "status": "processing"}), 202

if __name__ == '__main__':
    # Gunicorn handles this in production, but this is for local testing
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
