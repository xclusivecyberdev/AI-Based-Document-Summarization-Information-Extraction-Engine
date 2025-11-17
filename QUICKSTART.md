# Quick Start Guide

Get the AI Document Summarization Platform running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized deployment)

## Installation Methods

### Method 1: Quick Start Script (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd AI-Based-Document-Summarization-Information-Extraction-Engine

# Make the script executable (Linux/Mac)
chmod +x start.sh

# Run the startup script
./start.sh
```

The script will:
1. Create a virtual environment
2. Install all dependencies
3. Download required AI models
4. Initialize the database
5. Start the server

### Method 2: Docker (Easiest)

```bash
# Clone the repository
git clone <repository-url>
cd AI-Based-Document-Summarization-Information-Extraction-Engine

# Start with Docker Compose
docker-compose up --build
```

Access the platform at: http://localhost:8000

### Method 3: Manual Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd AI-Based-Document-Summarization-Information-Extraction-Engine

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# 5. Download AI models
python scripts/init_models.py

# 6. Create .env file
cp .env.example .env

# 7. Initialize database
python -c "from app.models.database import init_db; init_db()"

# 8. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## First Steps

### 1. Access the Platform

Open your browser and navigate to:
- **Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc

### 2. Create an Account

Using the API (cURL):
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password123"
  }'
```

Or use the interactive API docs at http://localhost:8000/api/docs

### 3. Login and Get Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure_password123"
```

Save the returned `access_token` for API requests.

### 4. Upload Your First Document

Using cURL:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@your_document.pdf"
```

Or use the web dashboard's upload interface.

### 5. Generate a Summary

```bash
curl -X POST "http://localhost:8000/api/summarize/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "file_id": "YOUR_FILE_ID",
    "method": "abstractive",
    "summary_length": "medium"
  }'
```

## Common Use Cases

### Summarize a PDF Document

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Login
response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "admin",
    "password": "secure_password123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload PDF
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/documents/upload", files=files, headers=headers)
    file_id = response.json()["file_id"]

# Generate Summary
response = requests.post(f"{BASE_URL}/summarize/", json={
    "file_id": file_id,
    "method": "abstractive",
    "summary_length": "medium"
}, headers=headers)

print(response.json()["summary"])
```

### Extract Information from Text

```python
response = requests.post(f"{BASE_URL}/analysis/extract", json={
    "text": "John Smith works at Acme Corp. Contact: john@example.com",
    "extract_persons": True,
    "extract_organizations": True,
    "extract_emails": True
}, headers=headers)

extracted = response.json()
print("Persons:", extracted["persons"])
print("Organizations:", extracted["organizations"])
print("Emails:", extracted["emails"])
```

### Perform OCR on an Image

```python
# Upload image
with open("scanned_document.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/documents/upload", files=files, headers=headers)
    file_id = response.json()["file_id"]

# Process with OCR
response = requests.get(f"{BASE_URL}/documents/{file_id}/process?use_ocr=true", headers=headers)
text = response.json()["result"]["text"]
print("Extracted text:", text)
```

## Available Features

✅ **Document Processing**
- PDF, DOCX, TXT, Images (PNG, JPG, TIFF)
- OCR for scanned documents (Tesseract & EasyOCR)
- Table extraction from PDFs

✅ **Summarization**
- Extractive: TextRank, LSA, LexRank, Luhn
- Abstractive: BART, T5 transformer models
- Multiple length options (short, medium, long)
- Bullet-point summaries

✅ **NLP Analysis**
- Named Entity Recognition (persons, organizations, locations)
- Keyword extraction (RAKE, YAKE, frequency-based)
- POS tagging
- Text statistics and readability scores

✅ **Information Extraction**
- Contact information (emails, phones, addresses)
- Dates and temporal expressions
- Monetary values and currencies
- Legal references
- Cybersecurity indicators (IPs, domains, CVEs)
- Medical terms

✅ **Advanced Features**
- Topic modeling (LDA, NMF)
- Document embeddings
- Similarity search
- Document clustering
- Visualizations (word clouds, charts)
- Export to DOCX/PDF

## API Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Create user account |
| `/api/auth/login` | POST | Get access token |
| `/api/documents/upload` | POST | Upload document |
| `/api/documents/{id}/process` | GET | Process document |
| `/api/summarize/` | POST | Generate summary |
| `/api/summarize/compare` | POST | Compare methods |
| `/api/analysis/nlp` | POST | NLP analysis |
| `/api/analysis/extract` | POST | Extract information |
| `/api/analysis/topics` | POST | Topic modeling |
| `/api/export/docx` | POST | Export to DOCX |
| `/api/export/pdf` | POST | Export to PDF |

## Troubleshooting

### Port 8000 already in use
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --port 8001
```

### ModuleNotFoundError
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Tesseract not found
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Set path in .env
TESSERACT_CMD=/usr/bin/tesseract
```

### Models not downloading
```bash
# Manually download models
python scripts/init_models.py

# Or download individually
python -m spacy download en_core_web_sm
```

### Out of memory
- Use extractive methods instead of abstractive
- Process smaller documents
- Reduce batch sizes
- Add more RAM or use GPU

## Next Steps

1. **Explore the API Documentation**: http://localhost:8000/api/docs
2. **Read the full README**: [README.md](README.md)
3. **Check API Examples**: [API_EXAMPLES.md](API_EXAMPLES.md)
4. **Review Performance Metrics**: [PERFORMANCE.md](PERFORMANCE.md)
5. **Deploy to Production**: [DEPLOYMENT.md](DEPLOYMENT.md)

## Resources

- **Documentation**: Full docs in README.md
- **Examples**: See API_EXAMPLES.md for detailed examples
- **Performance**: Performance benchmarks in PERFORMANCE.md
- **Deployment**: Production deployment guide in DEPLOYMENT.md
- **Tests**: Run tests with `pytest tests/`

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **API Docs**: Interactive documentation at `/api/docs`
- **Email**: support@example.com

## Quick Tips

💡 **For best summarization quality**: Use abstractive method with BART model
💡 **For fastest processing**: Use TextRank extractive method
💡 **For scanned documents**: Enable OCR with EasyOCR for better accuracy
💡 **For long documents**: Use chunking or extractive methods
💡 **For GPU acceleration**: Set `DEVICE=cuda` in .env

---

**You're all set! Start processing documents with AI! 🚀**
