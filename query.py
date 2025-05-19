from google.cloud import bigquery
import pandas as pd
from tabulate import tabulate

# Initialize the BigQuery client
client = bigquery.Client(project='bigquery-basics-460109')

# Define your SQL query
query = """
    SELECT word, ARRAY_AGG(sentence1 LIMIT 3) AS sentences
    FROM (
        SELECT word, sentence1,
               ROW_NUMBER() OVER (PARTITION BY word ORDER BY sentence1) as rn
        FROM `bigquery-basics-460109.rawc_data.rawc_table`
    )
    WHERE rn <= 3
    GROUP BY word
"""

# Execute the query
query_job = client.query(query)

# Fetch the results
results = query_job.result()

# Convert results to a DataFrame
rows = [dict(row) for row in results]
df = pd.DataFrame(rows)

# Split the sentences array into separate columns
df[['sentence1', 'sentence2', 'sentence3']] = pd.DataFrame(df['sentences'].tolist(), index=df.index)

# Drop the original sentences column
df.drop(columns=['sentences'], inplace=True)

# Print the DataFrame as a table using tabulate
print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
