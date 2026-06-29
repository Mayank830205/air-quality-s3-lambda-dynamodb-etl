# Air Quality Serverless ETL with CI/CD

A resume-ready serverless data engineering project based on the assignment brief: third-party air quality data is extracted, stored in S3, processed by Lambda, loaded into DynamoDB, and validated through GitHub Actions and AWS CodePipeline.

## Dataset Source

Open-Meteo Air Quality API

The project collects current air quality readings for Indian cities, including PM2.5, PM10, carbon monoxide, nitrogen dioxide, sulphur dioxide, ozone, and US AQI.

## Scenario

Clean city-level air quality readings and store the latest metrics in DynamoDB for simple analytics or dashboard use.

## Architecture

![Architecture](architecture.png)

```text
Open-Meteo Air Quality API
-> Python extraction script
-> raw JSON file
-> Amazon S3 raw/ prefix
-> AWS Lambda ETL function
-> Amazon DynamoDB clean_records table
-> CloudWatch audit logs
```

## AWS Services Used

- Amazon S3: stores raw files under the `raw/` prefix
- AWS Lambda: validates, transforms, and loads records
- Amazon DynamoDB: stores clean records
- Amazon CloudWatch: stores audit logs
- IAM: Lambda role with S3 read and DynamoDB write access
- GitHub Actions: validates code on push and pull request
- AWS CodePipeline and CodeBuild: source and build stages

## ETL Rules

Extract:
- Read raw JSON data from S3.

Transform:
- Reject records missing city, coordinates, timestamp, PM2.5, PM10, or AQI.
- Standardize `city` to uppercase.
- Convert numeric fields to DynamoDB-safe `Decimal` values.
- Add derived field `air_quality_status` from US AQI.

Load:
- Write clean records to DynamoDB.
- Use `record_id` as the partition key.
- `record_id` is built as `CITY#timestamp`.

Audit:
- Log total input records, inserted records, rejected records, and processing timestamp.

## DynamoDB Table Design

Table name: `clean_records`

| Attribute | Type | Purpose |
| --- | --- | --- |
| record_id | String | Partition key, unique city reading id |
| city | String | Standardized city name |
| timestamp | String | Source reading timestamp |
| pm25 | Number | PM2.5 value |
| pm10 | Number | PM10 value |
| air_quality_index | Number | US AQI value |
| air_quality_status | String | Derived AQI category |
| processed_at_utc | String | Lambda processing timestamp |

Recommended capacity mode: On-demand.

## Project Structure

```text
etl-s3-lambda-dynamodb/
|-- README.md
|-- lambda_function.py
|-- requirements.txt
|-- buildspec.yml
|-- sample_data/
|   |-- sample_raw_data.json
|   |-- sample_raw_data.csv
|-- extraction/
|   |-- config.py
|   |-- extract.py
|   |-- main.py
|   |-- upload_to_s3.py
|-- tests/
|   |-- test_lambda_function.py
|-- screenshots/
|-- .github/
|   |-- workflows/
|       |-- ci.yml
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest
```

Validate Lambda syntax:

```bash
python -m py_compile lambda_function.py
```

Extract fresh Open-Meteo data locally:

```bash
python extraction/main.py
```

Upload the latest raw JSON file to S3:

```bash
python extraction/upload_to_s3.py
```

## Lambda Setup

Handler:

```text
lambda_function.lambda_handler
```

Environment variables:

```text
TABLE_NAME=clean_records
BUCKET_NAME=cities-air-quality-bucket
OBJECT_KEY=raw/air_quality_raw_sample.json
AWS_REGION=us-east-1
```

For an S3 trigger, Lambda reads the bucket and object key from the event. `BUCKET_NAME` and `OBJECT_KEY` are useful for manual test events.

## GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on push and pull request. It checks out the repo, sets up Python 3.11, installs dependencies, validates `lambda_function.py` syntax, and runs the tests.

## AWS CodePipeline

CodePipeline should include:

- Source stage: GitHub repository
- Build stage: AWS CodeBuild using `buildspec.yml`

The buildspec installs dependencies, compiles `lambda_function.py`, and outputs `lambda_function.py` plus `requirements.txt` as build artifacts.

## Security Notes

Do not commit:

- AWS access keys or secret keys
- `.env` files
- AWS credentials files
- Generated zip files
- Large raw datasets
- `__pycache__/` or local virtual environments

## Required Screenshots

Add these under `screenshots/` before submission:

- Raw file in S3
- Lambda execution or CloudWatch logs
- Clean records in DynamoDB
- Successful GitHub Actions run
- Successful AWS CodePipeline run

## Reflection Answers

Why DynamoDB?
DynamoDB is serverless, simple to operate, and works well for latest city-level lookup records.

What is the partition key?
`record_id`, built as `CITY#timestamp`, because each city reading at a timestamp should be unique.

What transformations does Lambda apply?
It validates required fields, standardizes city names, converts numbers to Decimal, and derives `air_quality_status`.

What does GitHub Actions validate?
It validates Python syntax and runs unit tests.

What does CodePipeline do?
It pulls code from GitHub and runs CodeBuild to validate and package the Lambda source artifact.

Which files should never be committed?
Secrets, `.env`, credentials, generated zip files, cache files, virtual environments, and large raw data files.
