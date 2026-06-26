import base64
import json
import re
import functions_framework
from flask import abort
from google.cloud import bigquery
#  
#   
#   
# Initialize the BigQuery client outside the handler for faster performance (warm starts)
bq_client = bigquery.Client()
print("AT LEAST THIS PART GETS EXECUTED")
@functions_framework.http
def hello_pubsub(request):
    print("THE FUNCTION HELLO_PUBSUB STARTS")
    request_json = request.get_json(silent=True)

    if request_json is None or 'message' not in request_json:
        abort(400, description="Bad Request: 'message' field is missing")

    message_json = request_json['message']

    if message_json is None or 'data' not in message_json:
        abort(400, description="Bad Request: Pub/Sub message or data field is missing")

    encoded_data = message_json['data']
    try:
        # 1. Decode the incoming Pub/Sub message bytes into text
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        print(f"Decoded metadata payload: {decoded_data}")
        
        # 2. Parse the custom JSON string
        data_payload = json.loads(decoded_data)
        bucket_name = data_payload.get('bucket')
        file_name = data_payload.get('name') 
        
        if not bucket_name or not file_name:
            print("Error: Received payload, but 'bucket' or 'name' fields are missing.")
            return "Missing file metadata", 400

        print(f"Target file discovered: gs://{bucket_name}/{file_name}")

        # 3. Dynamic Table Logic
        # Example: "landing_zone/products/products8.csv" -> table_id = "products"
        path_parts = file_name.split('/')
        if len(path_parts) > 1:
            # Use the name of the immediate parent folder
            raw_name = path_parts[-2]
        else:
            # Fallback: Use filename without extension or numbers if no folder exists
            raw_name = re.sub(r'[\d.]', '', path_parts[-1]).split('.')[0]
        
        # Clean the name to ensure it's BigQuery compatible (lowercase, underscores)
        table_id = re.sub(r'[^a-zA-Z0-9_]', '_', raw_name).lower()
        if not table_id: table_id = "default_ingest"

        project_id = bq_client.project
        dataset_id = "csv_silver_tables"
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        # 4. Set up the automated CSV loader config
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,      # Skip the CSV header row
            autodetect=True,          # Automatically infer types
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            # Robustness options:
            allow_quoted_newlines=True, 
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION # Allow new columns as they appear
            ]
        )
        
        gcs_uri = f"gs://{bucket_name}/{file_name}"
        
        # 5. Execute the serverless transfer
        print(f"Launching direct BigQuery load job into {table_ref} from {gcs_uri}...")
        load_job = bq_client.load_table_from_uri(
            gcs_uri, table_ref, job_config=job_config
        )
        
        # Wait for BigQuery to finish processing the file
        load_job.result()
        print(f"Successfully ingested {file_name} into table {table_ref}!")
        
        return "OK", 200

    except Exception as e:
        print(f"Error processing Pub/Sub message: {e}")
        # Return 500 so Pub/Sub retries if it's a transient error
        abort(500, description=str(e))



# Now we force it