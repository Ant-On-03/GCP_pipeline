import functions_framework
import json
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()

PROJECT_ID = "project-64048d36-9702-43b2-805"
TOPIC_ID = "etl--csv-input-topic"

# 1. Change the decorator to .http instead of .cloud_event
@functions_framework.http
def hello_gcs(request):
    # 2. Extract the JSON payload safely from the HTTP request body
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return "No data received", 400

    # Extract the metadata from the raw payload
    bucket = request_json.get("bucket")
    name = request_json.get("name")
    timeCreated = request_json.get("timeCreated")
    event_type = request.headers.get("ce-type", "gcs-notification") # Fallback if header missing

    print(f"CODE STARTED, TRIGGERED BY {name} in bucket: {bucket}")

    message_dict = {
        "bucket": bucket,
        "name": name,
        "timeCreated": timeCreated,
        "event_type": event_type
    }

    message_bytes = json.dumps(message_dict).encode("utf-8")
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    print("LETS TRY PUBLISHING ON PUB/SUB")
    try:
        future = publisher.publish(topic_path, data=message_bytes)
        message_id = future.result()
        print(f"YEEEEEEEEEEEEEEES! WE GOT PUB/SUB RIGHT MESSAGE {message_id} tO {TOPIC_ID}.")
        return "OK", 200 # Return a success HTTP response
        
    except Exception as e:
        print(f"NOOOOOOOOOOOOOOOOO! THIS SUCKS PUB/SUB NOT BE WORKING {e}")
        return f"Internal Error: {e}", 500