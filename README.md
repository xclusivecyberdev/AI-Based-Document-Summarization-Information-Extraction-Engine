# AI-Based Document Summarization and Information Extraction Engine

A comprehensive AI-powered platform for processing, summarizing, and extracting information from documents including PDFs, Word documents, images, and scanned documents.

## Features

### Document Processing
- **Multi-format Support**: PDF, DOCX, TXT, PNG, JPG, JPEG, TIFF, BMP
- **OCR Integration**: Tesseract and EasyOCR for scanned documents
- **Advanced Text Extraction**: Table extraction, metadata parsing, structure analysis

### NLP Pipeline
- **Text Preprocessing**: Cleaning, tokenization, chunking
- **POS Tagging**: Part-of-speech analysis
- **Named Entity Recognition**: Extract persons, organizations, locations, dates
- **Keyword Extraction**: RAKE, YAKE, frequency-based methods
- **Topic Modeling**: LDA, NMF, Gensim-based topic extraction
- **Contextual Embeddings**: BERT, Sentence-BERT embeddings

### Summarization Models
- **Extractive Methods**:
  - TextRank
  - LSA (Latent Semantic Analysis)
  - LexRank
  - Luhn algorithm

- **Abstractive Methods**:
  - BART (facebook/bart-large-cnn)
  - T5
  - Custom transformer models

- **Summary Lengths**:
  - Short summary (10-15% of original)
  - Medium summary (20-30% of original)
  - Long summary (40-50% of original)
  - Custom bullet points

### Information Extraction
- **Entities**: Names, organizations, locations
- **Temporal**: Dates, time expressions
- **Financial**: Monetary values, currencies
- **Contact**: Emails, phone numbers, addresses
- **Legal**: Case citations, statutes, legal references
- **Cybersecurity**: IP addresses, domains, file hashes, CVE IDs
- **Medical**: Medical terms, ICD codes, dosages

### API & Dashboard
- **RESTful API**: FastAPI-based with OpenAPI documentation
- **Authentication**: JWT-based user authentication
- **Web Dashboard**: Interactive UI for document processing
- **Visualizations**: Word clouds, entity charts, topic distributions
- **Export**: DOCX and PDF export functionality

## Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Poppler (for PDF processing)

### Quick Start with Docker

```bash
# Clone repository
git clone <repository-url>
cd AI-Based-Document-Summarization-Information-Extraction-Engine

# Build and run with Docker Compose
docker-compose up --build
```

The application will be available at `http://localhost:8000`

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Install Tesseract OCR (system-level)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# macOS:
brew install tesseract poppler

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run the application
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

#### Authentication
```bash
# Register user
POST /api/auth/register
{
  "username": "user",
  "email": "user@example.com",
  "password": "password"
}

# Login
POST /api/auth/login
Form data: username, password
```

#### Document Upload
```bash
# Upload document
POST /api/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

# Process document
GET /api/documents/{file_id}/process?use_ocr=true
```

#### Summarization
```bash
# Generate summary
POST /api/summarize/
{
  "text": "Your text here...",
  "method": "abstractive",
  "summary_length": "medium",
  "include_bullets": false
}

# Compare methods
POST /api/summarize/compare

# Bullet summary
POST /api/summarize/bullets
```

#### NLP Analysis
```bash
# Analyze text
POST /api/analysis/nlp
{
  "text": "Your text...",
  "include_entities": true,
  "include_keywords": true
}

# Extract information
POST /api/analysis/extract
{
  "text": "Your text...",
  "extract_persons": true,
  "extract_organizations": true,
  "extract_dates": true
}

# Topic modeling
POST /api/analysis/topics
{
  "text": "Your text...",
  "num_topics": 5,
  "method": "lda"
}

# Generate embeddings
POST /api/analysis/embeddings
{
  "texts": ["text1", "text2"]
}
```

#### Export
```bash
# Export to DOCX
POST /api/export/docx
{
  "content": "Summary text...",
  "include_metadata": true
}

# Export to PDF
POST /api/export/pdf

# Generate word cloud
POST /api/export/visualize/wordcloud
```

## Usage Examples

### Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"

# Register and login
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
})

# Login
response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "testuser",
    "password": "password123"
})
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Upload document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/documents/upload", files=files, headers=headers)
    file_id = response.json()["file_id"]

# Summarize
response = requests.post(f"{BASE_URL}/summarize/", json={
    "file_id": file_id,
    "method": "abstractive",
    "summary_length": "medium"
}, headers=headers)

summary = response.json()["summary"]
print(summary)
```

### cURL Example

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"pass"}'

# Upload document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"

# Summarize text
curl -X POST http://localhost:8000/api/summarize/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"text":"Your long text here...","method":"abstractive","summary_length":"medium"}'
```

## Architecture

```
├── app/
│   ├── api/                    # API endpoints
│   │   ├── auth.py            # Authentication
│   │   ├── documents.py       # Document upload/management
│   │   ├── summarization.py   # Summarization endpoints
│   │   ├── analysis.py        # NLP analysis endpoints
│   │   └── export.py          # Export & visualization
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Settings
│   │   └── security.py        # Authentication utilities
│   ├── models/                 # Database models
│   │   └── database.py
│   ├── schemas/                # Pydantic schemas
│   │   └── schemas.py
│   ├── services/               # Business logic
│   │   ├── document_processor.py      # Document processing
│   │   ├── ocr_service.py             # OCR
│   │   ├── nlp_pipeline.py            # NLP preprocessing
│   │   ├── extractive_summarizer.py   # Extractive methods
│   │   ├── abstractive_summarizer.py  # Abstractive methods
│   │   ├── information_extractor.py   # Information extraction
│   │   ├── topic_modeling.py          # Topic modeling
│   │   ├── export_service.py          # Export utilities
│   │   └── visualization_service.py   # Visualizations
│   └── main.py                 # FastAPI application
├── templates/                  # HTML templates
│   └── dashboard.html
├── static/                     # Static files
├── uploads/                    # Uploaded documents
├── processed/                  # Processed files
├── logs/                       # Application logs
├── tests/                      # Unit tests
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Performance Metrics

### Summarization Quality
- **ROUGE Scores**: Evaluate summary quality
- **Compression Ratio**: Track summary length vs original
- **Processing Time**: Monitor performance

### Supported Document Sizes
- **Text**: Up to 1M characters
- **PDFs**: Up to 1000 pages
- **Images**: Up to 4096x4096 pixels
- **File Upload**: Max 50MB

## Model Information

### Pre-trained Models Used
- **Summarization**: facebook/bart-large-cnn, T5
- **NER**: spaCy en_core_web_sm
- **Embeddings**: all-MiniLM-L6-v2 (Sentence-BERT)
- **OCR**: Tesseract 4.0+, EasyOCR

### Customization
Models can be changed in `.env`:
```
DEFAULT_SUMMARIZATION_MODEL=facebook/bart-large-cnn
DEFAULT_NER_MODEL=en_core_web_sm
DEVICE=cpu  # or cuda for GPU
```

## Dataset Suggestions

For training or fine-tuning:
- **CNN/Daily Mail**: News summarization
- **PubMed**: Scientific paper summarization
- **arXiv**: Research paper summarization
- **MultiNews**: Multi-document summarization
- **BookSum**: Long document summarization

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_summarization.py -v
```

## Deployment

### Production Considerations
1. Change `SECRET_KEY` in `.env`
2. Set `DEBUG=False`
3. Use PostgreSQL instead of SQLite
4. Enable HTTPS
5. Configure CORS properly
6. Set up reverse proxy (nginx)
7. Use GPU for better performance

### Environment Variables
```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Optional
DEVICE=cuda  # Use GPU
MAX_UPLOAD_SIZE=104857600  # 100MB
DEFAULT_SUMMARIZATION_MODEL=facebook/bart-large-cnn
```

## Troubleshooting

### Common Issues

**Tesseract not found:**
```bash
# Set in .env
TESSERACT_CMD=/usr/bin/tesseract
```

**Out of memory:**
- Reduce batch sizes
- Use smaller models
- Enable chunking for long documents

**Slow processing:**
- Use GPU (set DEVICE=cuda)
- Reduce document size
- Use extractive methods instead of abstractive

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Citation

If you use this platform in your research, please cite:

```bibtex
@software{document_ai_platform,
  title={AI-Based Document Summarization and Information Extraction Engine},
  year={2024},
  url={https://github.com/yourusername/document-ai-platform}
}
```

## Support

- **Documentation**: See `/api/docs`
- **Issues**: GitHub Issues
- **Email**: support@example.com

## Acknowledgments

- Hugging Face Transformers
- spaCy
- FastAPI
- Tesseract OCR
- EasyOCR
- All open-source contributors

---

**Version**: 1.0.0
**Last Updated**: 2024
**Author**: AI Document Platform Team
