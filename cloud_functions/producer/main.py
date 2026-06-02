import functions_framework
import json
from google.cloud import pubsub_v1

# Initialize the publisher client outside the main function. 
# This is a best practice so the client is reused across "warm" function calls, saving time and memory.
publisher = pubsub_v1.PublisherClient()

# --- REPLACE THESE VARIABLES ---
PROJECT_ID = "project-64048d36-9702-43b2-805"
TOPIC_ID = "etl--csv-input-topic" 
# -------------------------------

@functions_framework.cloud_event
def hello_gcs(cloud_event):
    data = cloud_event.data

    # Extract the metadata
    bucket = data["bucket"]
    name = data["name"]
    timeCreated = data["timeCreated"]
    event_type = cloud_event["type"]

    print(f"CODE STARTED, TRIGGERED BY {name} in bucket: {bucket}")

    # 1. Package the specific data you want to send downstream into a dictionary
    message_dict = {
        "bucket": bucket,
        "name": name,
        "timeCreated": timeCreated,
        "event_type": event_type
    }

    # 2. Convert the dictionary to a JSON string, then encode it to bytes
    # (Pub/Sub requires the payload to be a byte string)
    message_bytes = json.dumps(message_dict).encode("utf-8")

    # 3. Construct the full topic path
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    # 4. Publish the message to Pub/Sub
    print("LETS TRY PUBLISHING ON PUB/SUB")
    try:
        # The publish method returns a "future" object
        future = publisher.publish(topic_path, data=message_bytes)
        
        # Calling .result() forces the function to wait until the publish succeeds, returning the message ID
        message_id = future.result() 
        print(f"YEEEEEEEEEEEEEEES! WE GOT PUB/SUB RIGHT MESSAGE {message_id} tO {TOPIC_ID}.")
        
    except Exception as e:
        print(f"NOOOOOOOOOOOOOOOOO! THIS SUCKS PUB/SUB NOT BE WORKING {e}")
        # Re-raise the exception so the Cloud Function registers this as a failed execution
        raise e