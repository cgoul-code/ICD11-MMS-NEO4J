# ICD-11 Entity and Linearization API Interaction Script

This Python script interacts with the International Classification of Diseases (ICD-11) API to fetch and process medical classification data. Using the Foundation, it traverses 26 chapters for the MMS classification (83.585 foundation entities) and creates the MMS-reporting codes (12.409 linearization entities)
It uses the WHO's ICD-11 API to retrieve foundation and linearization entities and integrates this data into a Neo4j graph database.

This application serves as a demonstrative example to test the capabilities of Knowledge Graphs used in combination with OpenAI. 
It has been developed by HELSEDIREKTORATET (the Norwegian Directorate of Health) as part of the 'HelseSvar' project.

## Features

- Fetches ICD-11 Foundation entities based on specific URIs.
- If the Foundation entity has a matching MMS-entity from MMS linerization, then create a node in the graph database
- Parses and processes data including titles, definitions, and diagnostic criteria.
- Utilizes regular expressions to extract and clean data.
- Manages API authentication and session handling with token-based access.
- Logs data processing steps and potential errors for troubleshooting.
- Saves fetched data and logs into CSV files.
- Conditionally builds a graph database structure in Neo4j based on the fetched data.

## Requirements

- Python 3.x
- Neo4j Database
- Python libraries:
  - `requests`
  - `os`
  - `re`
  - `certifi`
  - `urllib3`
  - `csv`
  - `json`
  - `typing`
  - `time`
  - `dotenv`
  - `neo4j`

Ensure that the required libraries are installed using:
```bash
pip install requests certifi urllib3 python-dotenv neo4j
```

## Setup

1. **Neo4j Database:**
   - Ensure that Neo4j is installed and running. [Setup instructions](https://neo4j.com/docs/api/python-driver/current/).
   - Configure the connection parameters (`NEO_URI`, `NEO_USER`, and `NEO_PASSWORD`) in your `.env` file.

2. **ICD API Access:**
   - Register at [WHO ICD API Management](https://icd.who.int/icdapi) to obtain `ClientID` and `ClientSecret`.
   - Store these credentials in your `.env` file.

3. **Environment Variables:**
   - Create a `.env` file in the root directory of the script.
   - Include the following environment variables:
     ```
     ICD_CLIENT_ID='your-client-id'
     ICD_CLIENT_SECRET='your-client-secret'
     NEO_URI='bolt://localhost:7687'
     NEO_USER='neo4j'
     NEO_PASSWORD='your-password'
     ```

## Usage

Execute the script by running:
```bash
python icd11_neo4j_integration.py
```

## Output

- `MMS_ICD11_transaction_log.csv`: Contains processed data in a structured format.
- `MMS_ICD11_log.csv`: Contains log entries for debugging and error tracking.

## Links

- [ICD-11 API Documentation](https://id.who.int/swagger/index.html)
- [ICD-11 Official Documentation](https://icd.who.int/browse/2024-01/mms/en#402520533)
- [Neo4j Python Driver](https://neo4j.com/docs/api/python-driver/current/)

## Author

- [Christian Goulignac for  HELSEDIREKTORATET (the Norwegian Directorate of Healt)]


