# ⚙️ CI/CD Setup Guide

Follow these steps to configure the CI/CD pipeline for automatic deployment of the **Air Quality ETL Pipeline**.

---

## 1. Clone the Repository

```bash
git clone https://github.com/Mayank830205/air-quality-s3-lambda-dynamodb-etl.git
cd air-quality-s3-lambda-dynamodb-etl
```

---

## 2. Create an AWS Lambda Function

* Open **AWS Console**
* Navigate to **Lambda**
* Click **Create Function**
* Select **Author from scratch**
* Function Name: `air-quality-s3-lambda-dynamodb-etl`
* Runtime: **Python 3.12**
* Click **Create Function**

---

## 3. Create an IAM Role

Attach the following permissions:

* Amazon S3 (Read Access)
* Amazon DynamoDB (Read/Write)
* CloudWatch Logs

Recommended AWS Managed Policies:

* `AmazonS3ReadOnlyAccess`
* `AmazonDynamoDBFullAccess`
* `AWSLambdaBasicExecutionRole`

---

## 4. Configure Lambda Environment Variables

| Variable   | Example       |
| ---------- | ------------- |
| TABLE_NAME | clean_records |

> **Note:** If Lambda is triggered by an S3 event, `BUCKET_NAME` and `OBJECT_KEY` are read from the event and do **not** need to be configured as environment variables.

---

## 5. Configure S3 Trigger

Create an S3 bucket, for example:

```
cities-air-quality-bucket
```

Create a folder:

```
raw/
```

Add an **ObjectCreated** event notification:

```
Amazon S3
      │
      ▼
ObjectCreated Event
      │
      ▼
AWS Lambda
```

Whenever a new JSON file is uploaded to the `raw/` folder, Lambda will automatically start the ETL process.

---

## 6. Create a CodeBuild Project

| Setting          | Value                            |
| ---------------- | -------------------------------- |
| Source           | No Source (used by CodePipeline) |
| Environment      | Managed Image                    |
| Operating System | Ubuntu                           |
| Runtime          | Standard                         |
| Image            | aws/codebuild/standard:7.0       |
| Runtime Version  | Python 3.12                      |
| Buildspec        | `buildspec.yml`                  |

---

## 7. Add `buildspec.yml`

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.12
    commands:
      - mkdir package
      - pip install -r lambda/requirements.txt -t package

  build:
    commands:
      - cp lambda/*.py package/
      - cd package
      - zip -r ../function.zip .

artifacts:
  files:
    - function.zip
```

---

## 8. Create AWS CodePipeline

### Source Stage

* Provider: **GitHub (GitHub App)**
* Repository: `Mayank830205/air-quality-s3-lambda-dynamodb-etl`
* Branch: `main`

### Build Stage

* Provider: **AWS CodeBuild**
* Project: `air-quality-etl-build`

### Deploy Stage

* Provider: **AWS Lambda**
* Function:

```
air-quality-s3-lambda-dynamodb-etl
```

---

## 9. Configure GitHub Actions

Workflow:

```
.github/workflows/ci.yml
```

The workflow will:

* Install dependencies
* Run pytest unit tests
* Validate Lambda syntax
* Ensure the ETL pipeline is ready for deployment

---

## 10. Push the Code

```bash
git add .
git commit -m "Air Quality ETL Update"
git push origin main
```

---

## 11. Automatic Deployment Flow

```
GitHub Repository
        │
        ▼
GitHub Actions (CI)
        │
        ▼
AWS CodePipeline
        │
        ▼
AWS CodeBuild
        │
        ▼
AWS Lambda Deployment
```

---

# ✅ Verify Deployment

Modify:

```python
lambda/lambda_function.py
```

Add:

```python
print("Air Quality ETL Deployment Successful!")
```

Commit and push:

```bash
git add .
git commit -m "Verify deployment"
git push origin main
```

Verify the following:

* ✅ GitHub Actions completed successfully
* ✅ AWS CodePipeline completed successfully
* ✅ AWS CodeBuild completed successfully
* ✅ Lambda **Last Modified** timestamp updated
* ✅ CloudWatch Logs contain:

```
========== Air Quality ETL Pipeline Started ==========
Reading data from S3...
Processing records...
Data successfully loaded into DynamoDB
========== Air Quality ETL Pipeline Completed ==========
```

---

# Deployment Architecture

```
Open-Meteo Air Quality API
          │
          ▼
Python Extract Script
          │
          ▼
data/raw/air_quality_raw.json
          │
          ▼
Amazon S3 (raw/)
          │
          ▼
S3 ObjectCreated Event
          │
          ▼
AWS Lambda ETL
          │
          ▼
Amazon DynamoDB (clean_records)
          │
          ▼
CloudWatch Logs

                ▲
                │
GitHub → GitHub Actions → CodePipeline → CodeBuild
```
