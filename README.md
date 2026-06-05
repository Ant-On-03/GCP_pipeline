# GCP Serverless Data Ingestion Pipeline (Bronze to Silver)

An event-driven, decoupled, and serverless Google Cloud pipeline designed to automatically ingest raw CSV files from a "bronze" Cloud Storage landing bucket into a "silver" BigQuery dataset.

## **Architecture & UML Diagrams**

The following UML/C4 diagrams illustrate the architecture, event flow, and code deployment strategy for this pipeline.

### 1. System Context
*The high-level flow of events from the Cloud Storage Bucket to the BigQuery Data Warehouse.*
![Context Diagram](doc/C4-Context-Diagram-Events-Pipeline.svg)

### 2. Application Architecture
*The internal components of the cleaning pipeline, highlighting the Producer-Broker-Worker pattern.*
![Application Diagram](doc/C4-Cleaning-Pipeline-App-Diagram.svg)

### 3. Code & Cloud Build Context
*Repository structure and deployment flow mapping from GitHub to the GCP infrastructure.*
![Code Diagram](doc/C4-Github-Code-App-Diagram.svg)

### 4. Data Ingestion Sequence
*A step-by-step sequence of events from the initial CSV upload by the actor to the final data load into BigQuery.*
![Sequence Diagram](doc/SequenceUML-DataIngestionFlow.drawio.svg)

---

## **How It Works (The "What")**

The pipeline is triggered by csv ingestion, so whenever a csv in uploaded manually or automatically to the gcp bucket, it automattically triggers a servless cloud function that queues the job as an event in a Pub/Sub topic.

The broker (Cloud Pub/Sub) acts as the buffer. Recieves the event and lets workers pull it.

Another function (the worker) consumes that topic. It is a pipeline that injest the tables into BigQuery.

the worker performs table name cleaning, dynamic table creation/detection. It then issues a direct `load_table_from_uri` job to BigQuery, appending the data to the `csv_silver_tables` dataset while allowing for automatic schema updates.

No idempotency assurance is performed in the pipeline.



## **Design Rationale (The "Why")**

The pipeline is designed to be scalable, simple, decoupled and asyncronous. 

Queue-like behaviour:
By having a cloud function publish events, we ensure no bottlenecks on getting the data published. It is a lightweight function that just ensures the job will eventually get done. If bigquery fails or we get a massive dump at once, the jobs dont get lost, they just stay in the queue for longer.

The worker consuming the topic does the heavy lifting. It can easily be scaled to perform complex ETL operations.

Serverless:
Cloud functions' containers only get deployed whenever triggered, reducing cloud costs.

## Future Improvements

- Add idempotency controls
- Add dead-letter topics
- Migrate transformation logic to Dataflow
- Explore Dataplex AI agents and identify opportunities for new capabilities

## **Setup & Deployment**

### Prerequisites
* Google Cloud Project.
* Cloud Pub/Sub Topic: `etl--csv-input-topic`.
* BigQuery Dataset: `csv_silver_tables`.

### Dependencies
Both functions require Python 3.x and the `functions-framework==3.*`. 
* **Worker** utilizes `google-cloud-bigquery` for data loading.
* **Producer** utilizes `google-cloud-pubsub==2.*` for event messaging.

### Environment
* Ensure the service accounts running these Cloud Functions have the necessary IAM roles (`roles/pubsub.publisher` for the Producer, and `roles/bigquery.dataEditor` / `roles/storage.objectViewer` for the Worker).
