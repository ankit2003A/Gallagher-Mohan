# Gallagher and Mohan - Invoice Processing System

A full-stack application for processing and managing invoices using OCR and LLM technologies.

## Features

- User authentication and authorization
- Invoice upload and processing
- OCR (Optical Character Recognition) for text extraction
- LLM-powered data extraction and validation
- Secure file storage
- RESTful API backend
- Responsive frontend

## Tech Stack

### Backend
- Python 3.8+
- FastAPI
- SQLAlchemy (ORM)
- PostgreSQL
- Pydantic (Data validation)
- JWT Authentication
- Tesseract OCR
- Pytest (Testing)

### Frontend
- React.js
- TypeScript
- Tailwind CSS
- React Query
- Axios

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Tesseract OCR
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone [https://github.com/ankit2003A/gallaghermohan.git](https://github.com/ankit2003A/gallaghermohan.git)
   cd gallaghermohan

### Backend Setup
   ```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
### Frontend Setup
   ```bash
cd ../frontend
npm install
npm start
   ```
### Usage
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### API Documentation
Once the backend is running, access the interactive API documentation at:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

