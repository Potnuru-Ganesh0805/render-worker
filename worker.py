import os
import json
import time
import requests
import redis
from ultralytics import YOLO
from PIL import Image
from io import BytesIO

# Connect to Redis using the URL from your Render environment variable
redis_client = redis.from_url(os.environ.get("REDIS_URL"))

# Load the YOLOv8 model once
model = YOLO("yolov8n.pt") # You can also use your custom model file

# The detection classes you are interested in
target_classes = ['person', 'light_on', 'light_off']

def process_job(job_data):
    try:
        image_url = job_data['image_url']
        webhook_url = job_data['webhook_url']

        print(f"Processing job for image: {image_url}")

        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # Run YOLOv8 prediction
        results = model.predict(source=image, conf=0.25)
        
        # Extract and count detections for the target classes
        detections = {cls: {'count': 0, 'locations': []} for cls in target_classes}
        for result in results:
            for box in result.boxes:
                # Get class name and bounding box coordinates
                class_id = int(box.cls)
                class_name = model.names[class_id]
                
                if class_name in target_classes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections[class_name]['count'] += 1
                    detections[class_name]['locations'].append([x1, y1, x2, y2])

        # Prepare and send the response to the webhook
        payload = {
            "status": "completed",
            "image_url": image_url,
            "detections": detections
        }
        
        requests.post(webhook_url, json=payload)
        print("Response sent to webhook successfully.")

    except Exception as e:
        print(f"Error processing job: {e}")
        # Optionally, send an error response to the webhook
        requests.post(webhook_url, json={"status": "error", "message": str(e)})

if __name__ == "__main__":
    print("Worker started. Listening for jobs...")
    while True:
        # Block and wait for a new job from the queue
        job = redis_client.brpop('detection_jobs', timeout=10)
        if job:
            job_data = json.loads(job[1])
            process_job(job_data)
        else:
            time.sleep(1) # Sleep to prevent excessive polling if the queue is empty
