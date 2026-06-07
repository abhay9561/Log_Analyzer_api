# Log Analyzer API

## Overview

Log Analyzer API is a production-ready FastAPI application that analyzes large transaction log files and identifies suspicious transactions.

This project refactors a legacy Python implementation that suffered from Out-Of-Memory (OOM) issues due to loading entire files into memory using `readlines()`. The refactored solution uses Python Generators, Object-Oriented Programming (OOP), Exception Handling, Structured Logging, and FastAPI to provide a scalable and memory-efficient log analysis service.

---

## Video Walkthrough

A complete walkthrough of the project, architecture, implementation, API demonstration, and testing.

🎥 Video Link:
https://drive.google.com/file/d/1Zqcb4ohE7hXeUmyF-ww_QQiD9VuLENWx/view?usp=sharing

---

## Problem Statement

The legacy implementation had the following issues:

* Loaded the entire file into memory using `readlines()`
* Crashed with OOM errors when processing large files (50GB+)
* Poor code structure and maintainability
* No exception handling
* No production logging
* No API interface

The objective was to refactor the solution into a production-ready service capable of processing large log files efficiently.

---

## Key Features

* Object-Oriented Design (OOP)
* Generator-Based Streaming Processing
* Memory-Efficient Large File Handling
* FastAPI REST API
* Structured JSON Responses
* Production-Grade Logging
* Robust Exception Handling
* File Upload Support
* Swagger API Documentation
* Unit Testing with Pytest
* Support for Large Log Files (50GB+)

---

## Project Structure

```text
log-analyzer/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   └── test_main.py
│
├── sample_logs/
│   └── test.log
│
├── generate_sample_log.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Technologies Used

* Python 3.10+
* FastAPI
* Uvicorn
* Pydantic
* Pytest
* Python Logging Module
* Dataclasses
* Generators

---

## Application Flow

```text
User Uploads Log File
        ↓
FastAPI Endpoint (/analyze-logs)
        ↓
LogAnalyzer Class
        ↓
Generator-Based Processing
        ↓
Apply Business Rules
        ↓
Flag Suspicious Transactions
        ↓
JSON Response
```

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd log-analyzer
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Generate Sample Log File

Generate a sample log file with 1000 records:

```bash
python generate_sample_log.py 1000
```

Output:

```text
sample_logs/test.log
```

Example Record:

```text
2024-01-01 08:00:00,user_0043,45057.59,ERROR,Session expired
```

Format:

```text
timestamp,user_id,amount,log_level,message
```

---

## Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Application URL:

```text
http://127.0.0.1:8000
```

Swagger Documentation:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### POST /analyze-logs

Upload a `.log` or `.csv` file and retrieve flagged transactions.

#### Request

Content-Type:

```text
multipart/form-data
```

Field:

```text
file
```

#### Sample Response

```json
{
  "total_flagged": 111,
  "flagged_transactions": [
    {
      "user": "user_0043",
      "amount": 45057.59,
      "status": "flagged"
    }
  ],
  "errors_encountered": 0,
  "lines_processed": 1000
}
```

---

### GET /health

Health-check endpoint.

Response:

```json
{
  "status": "ok",
  "service": "log-analyzer"
}
```

---

### GET /

Returns API information.

Response:

```json
{
  "service": "Log Analyzer API",
  "version": "1.0.0"
}
```

---

## Business Logic

A transaction is flagged when:

```python
log_level == "ERROR" and amount > 10000
```

Example:

```text
2024-01-01,user_0042,15000.00,ERROR,Payment gateway timeout
```

Output:

```json
{
  "user": "user_0042",
  "amount": 15000.00,
  "status": "flagged"
}
```

---

## Complexity Analysis

### Legacy Implementation

```python
data = file.readlines()
```

Time Complexity:

```text
O(N)
```

Space Complexity:

```text
O(N)
```

Reason:

Entire file is loaded into memory, causing Out-Of-Memory failures for large files.

---

### Refactored Implementation

```python
for line in file:
```

or

```python
yield line
```

Time Complexity:

```text
O(N)
```

Space Complexity:

```text
O(K)
```

Where:

```text
K = Number of Flagged Transactions
```

The solution processes one line at a time, making it suitable for very large files.

---

## Logging & Error Handling

The application includes:

* Structured Logging
* Invalid Record Handling
* Numeric Conversion Validation
* Unsupported File Type Validation
* Missing File Validation
* Runtime Exception Handling

Supported HTTP Status Codes:

| Status Code | Description           |
| ----------- | --------------------- |
| 200         | Success               |
| 415         | Unsupported File Type |
| 422         | Validation Error      |
| 500         | Internal Server Error |

---

## Testing

Run all tests:

```bash
python -m pytest tests/ -v
```

Expected Result:

```text
22 passed
```

The test suite validates:

* OOP Model Behavior
* Generator Processing
* API Functionality
* Response Structure
* Validation Logic
* Error Handling
* Health Endpoint
* Root Endpoint

---

## Assignment Requirements Mapping

| Requirement         | Implementation                  |
| ------------------- | ------------------------------- |
| Refactoring         | Production-Ready Code Structure |
| OOP                 | LogAnalyzer Class + Dataclass   |
| Generator           | Streaming File Processing       |
| Context Manager     | Safe File Handling              |
| Exception Handling  | Try/Except Blocks               |
| Logging             | Python Logging Module           |
| FastAPI Endpoint    | POST /analyze-logs              |
| Complexity Analysis | Included in Code & README       |
| Unit Testing        | Pytest Test Suite               |

---

## Test Results

* Successfully Processes Large Log Files
* Eliminates OOM Issues
* Memory-Efficient Streaming Architecture
* 22/22 Unit Tests Passed
* Fully Functional FastAPI Service

---

## Author

**Abhay Tale**

AI/ML Engineer | Data Science Enthusiast | Python Developer


