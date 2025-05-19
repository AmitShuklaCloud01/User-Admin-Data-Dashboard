from google.cloud import bigquery

client = bigquery.Client(project='bigquery-basics-460109')

# Define the dataset ID
project_id = 'bigquery-basics-460109'
dataset_id = f'{project_id}.rawc_data'

# Create a Dataset object
dataset = bigquery.Dataset(dataset_id)

# Set the location (optional, default is US)
dataset.location = "US"

# Create the dataset
dataset = client.create_dataset(dataset, exists_ok=True)  # exists_ok=True prevents errors if the dataset already exists
print(f"Created dataset {client.project}.{dataset.dataset_id}")

# Define the table ID
table_id = f'{dataset_id}.rawc_table'

# Load data into the table
job_config = bigquery.LoadJobConfig(
    source_format=bigquery.SourceFormat.CSV,
    skip_leading_rows=1,  # Skip the header row if present
    autodetect=True,  # Enable schema autodetection
)

with open(r'C:\Users\amush\INLP_Project\Finetuning\raw-c.csv', 'rb') as source_file:
    load_job = client.load_table_from_file(source_file, table_id, job_config=job_config)

load_job.result()  # Wait for the job to complete

print(f"Loaded {load_job.output_rows} rows into {table_id}.")

# Display dataset and table information
print(f"Dataset: {dataset.dataset_id}")
