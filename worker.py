import os
import json
import time
import requests
import redis
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import torch
import torch.quantization

# Connect to the Redis instance
try:
    redis_client = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")
    redis_client = None

# Use the GPU if available, otherwise use CPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the model and apply quantization for a smaller memory footprint
print("Loading FP32 model...")
# It is recommended to download your model weights and put it in the same directory
# so Render's build can find it.
try:
    model = YOLO("yolov8n.pt").to(device)
    print("Applying dynamic quantization to reduce memory usage.")
    quantized_model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear, torch.nn.Conv2d}, dtype=torch.qint8
    )
    model = quantized_model
    print("Model loaded and quantized.")
except Exception as e:
    print(f"Error loading or quantizing model: {e}")
    model = None

# Define the classes to detect
TARGET_CLASSES = ['person', 'light_on', 'light_off']

def process_job(job_data):
    if model is None:
        print("Model is not loaded. Skipping job.")
        return

    try:
        image_url = job_data['image_url']
        webhook_url = job_data['webhook_url']

        print(f"Processing job for image: {image_url}")

        # Download the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # Run YOLOv8 prediction on the image
        results = model.predict(source=image, conf=0.25)

        # Extract detections for the target classes
        detections = {cls: {'count': 0, 'locations': []} for cls in TARGET_CLASSES}
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)
                class_name = model.names[class_id]
                
                if class_name in TARGET_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections[class_name]['count'] += 1
                    detections[class_name]['locations'].append([x1, y1, x2, y2])

        # Prepare and send the final response to the webhook
        payload = {
            "status": "completed",
            "image_url": image_url,
            "detections": detections
        }
        
        requests.post(webhook_url, json=payload)
        print("Response sent to webhook successfully.")

    except Exception as e:
        print(f"Error processing job: {e}")
        # Send an error payload to the webhook
        requests.post(webhook_url, json={"status": "error", "message": str(e)})

if __name__ == "__main__":
    if redis_client is None:
        print("Worker cannot start without a Redis connection.")
    else:
        print("Worker started. Listening for jobs...")
        while True:
            # brpop is a blocking pop, which waits for a job to appear in the queue
            job = redis_client.brpop('detection_jobs', timeout=10)
            if job:
                job_data = json.loads(job[1])
                process_job(job_data)
            else:
                # Sleep briefly if the queue is empty
                time.sleep(1)
