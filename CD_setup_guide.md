# CI/CD Setup Guide

This guide matches the serverless ETL assignment brief. Keep it simple: GitHub Source stage, CodeBuild Build stage, and screenshots for submission.

## 1. Lambda

Create one Lambda function.

- Runtime: Python 3.11 or Python 3.12
- Handler: `lambda_function.lambda_handler`
- Source file: `lambda_function.py`

Environment variables for manual tests:

```text
TABLE_NAME=air_quality_clean_records
BUCKET_NAME=cities-air-quality-bucket
OBJECT_KEY=raw/air_quality_raw_sample.json
```

If Lambda is triggered by S3, the bucket and object key come from the S3 event.

## 2. S3

Create one bucket and upload raw files under:

```text
raw/
```

Example object:

```text
raw/air_quality_raw_sample.json
```

## 3. DynamoDB

Create one table:

```text
air_quality_clean_records
```

Partition key:

```text
record_id String
```

Use on-demand capacity.

## 4. GitHub Actions

The workflow is in:

```text
.github/workflows/ci.yml
```

It installs dependencies, validates `lambda_function.py`, and runs tests.

## 5. CodePipeline

Create a pipeline with two required stages:

- Source: GitHub repository
- Build: AWS CodeBuild project using `buildspec.yml`

The buildspec validates `lambda_function.py` and publishes these artifacts:

```text
lambda_function.py
requirements.txt
```

## 6. Screenshots For Submission

Save screenshots in `screenshots/`:

- Raw file in S3
- Lambda execution or CloudWatch logs
- Clean records in DynamoDB
- Successful GitHub Actions run
- Successful AWS CodePipeline run
