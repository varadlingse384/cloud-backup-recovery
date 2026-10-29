# Cloud-Based Backup and Recovery System

## 1. Project Overview

The Cloud-Based Backup and Recovery System is a Python web application that uses Amazon S3 to store, manage, download, and recover backup files.

The application provides a simple interface using Streamlit and communicates with AWS through the Boto3 SDK.

## 2. Objectives

* Store backup files in cloud storage.
* Allow users to view and download backups.
* Maintain previous file versions.
* Recover earlier versions when required.
* Demonstrate cloud storage and recovery concepts.

## 3. Technologies Used

* Python
* Streamlit
* Boto3
* Amazon S3
* AWS IAM
* Visual Studio Code

## 4. Main Modules

1. Upload Backup
2. View Backups
3. Download Backup
4. Recover Previous Version
5. Delete Backup

## 5. Installation

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

Configure AWS credentials using an appropriate credential provider.

Set the bucket name and Region in the environment:

```text
S3_BUCKET_NAME=YOUR_BUCKET_NAME
AWS_REGION=ap-south-1
```

## 6. Run the Application

```bash
python -m streamlit run app.py
```

## 7. Expected Outcome

The application provides a basic interface for managing backup files stored in Amazon S3 and recovering earlier object versions.

## 8. Security

Keep S3 Block Public Access enabled, use restricted IAM permissions, and never store AWS secrets in the source code.
