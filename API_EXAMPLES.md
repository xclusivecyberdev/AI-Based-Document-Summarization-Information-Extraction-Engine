# API Examples and Use Cases

## Complete Workflow Examples

### Example 1: Process and Summarize a PDF Document

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Step 1: Register and login
# Register
requests.post(f"{BASE_URL}/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
})

# Login
response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "john_doe",
    "password": "secure_password123"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Upload PDF
with open("research_paper.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        files=files,
        headers=headers
    )

file_id = response.json()["file_id"]
print(f"File uploaded: {file_id}")

# Step 3: Process document (with OCR if needed)
response = requests.get(
    f"{BASE_URL}/documents/{file_id}/process",
    params={"use_ocr": False},
    headers=headers
)

processed = response.json()
print(f"Text extracted: {len(processed['result']['text'])} characters")

# Step 4: Generate summary
response = requests.post(
    f"{BASE_URL}/summarize/",
    json={
        "file_id": file_id,
        "method": "abstractive",
        "summary_length": "medium",
        "include_bullets": True
    },
    headers=headers
)

summary = response.json()
print("\nSummary:")
print(summary["summary"])
print(f"\nCompression: {summary['compression_ratio']:.2%}")

if summary.get("bullets"):
    print("\nKey Points:")
    for bullet in summary["bullets"]:
        print(bullet)

# Step 5: Export to DOCX
response = requests.post(
    f"{BASE_URL}/export/docx",
    json={
        "file_id": file_id,
        "content": summary["summary"],
        "include_metadata": True
    },
    headers=headers
)

with open("summary_export.docx", "wb") as f:
    f.write(response.content)

print("\nSummary exported to: summary_export.docx")
```

### Example 2: Extract Information from Legal Document

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Assuming already authenticated
headers = {"Authorization": f"Bearer {token}"}

legal_text = """
In the case of Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that...
The plaintiff, represented by John Smith of Smith & Associates LLP, filed suit on
January 15, 2019. The defendant is Acme Corporation, located at 123 Main Street,
New York, NY 10001. The case involves damages of $1,500,000. Contact attorney at
jsmith@smithlaw.com or (555) 123-4567 for more information.
"""

# Extract information
response = requests.post(
    f"{BASE_URL}/analysis/extract",
    json={
        "text": legal_text,
        "extract_persons": True,
        "extract_organizations": True,
        "extract_dates": True,
        "extract_monetary": True,
        "extract_emails": True,
        "extract_phones": True
    },
    headers=headers
)

extracted = response.json()

print("Persons Found:")
for person in extracted["persons"]:
    print(f"  - {person['name']}")

print("\nOrganizations:")
for org in extracted["organizations"]:
    print(f"  - {org['name']}")

print("\nDates:")
for date in extracted["dates"]:
    print(f"  - {date['text']} ({date['parsed']})")

print("\nMonetary Values:")
for money in extracted["monetary_values"]:
    print(f"  - {money['text']}")

print("\nContact Information:")
for email in extracted["emails"]:
    print(f"  Email: {email['email']}")

for phone in extracted["phone_numbers"]:
    print(f"  Phone: {phone['number']}")

print("\nLegal References:")
for ref in extracted["legal_references"]:
    print(f"  - {ref['text']} ({ref['type']})")
```

### Example 3: Topic Modeling and Clustering

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

# Long document text
document_text = """
[Your long document text here...]
"""

# Extract topics
response = requests.post(
    f"{BASE_URL}/analysis/topics",
    json={
        "text": document_text,
        "num_topics": 5,
        "method": "lda"
    },
    headers=headers
)

topics = response.json()

print("Discovered Topics:")
for topic in topics["topics"]:
    print(f"\nTopic {topic['topic_id']}:")
    print(f"  Top words: {topic['top_words_str']}")
    print(f"  Words: {', '.join(topic['words'][:10])}")

# Generate embeddings for similarity search
documents = [
    "Document about machine learning and AI",
    "Article about healthcare and medicine",
    "Text about financial markets and stocks",
]

response = requests.post(
    f"{BASE_URL}/analysis/embeddings",
    json={"texts": documents},
    headers=headers
)

embeddings = response.json()
print(f"\nGenerated embeddings: {embeddings['shape']}")

# Find similar documents
query = "artificial intelligence in healthcare"

response = requests.post(
    f"{BASE_URL}/analysis/similarity",
    json={
        "query": query,
        "documents": documents,
        "top_k": 2
    },
    headers=headers
)

similar = response.json()

print(f"\nQuery: {query}")
print("Most similar documents:")
for result in similar["results"]:
    print(f"  Rank {result['rank']}: {result['document'][:50]}...")
    print(f"  Similarity: {result['similarity']:.4f}")
```

### Example 4: Compare Summarization Methods

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

text = """
[Your text to summarize...]
"""

# Compare all methods
response = requests.post(
    f"{BASE_URL}/summarize/compare",
    json={
        "text": text,
        "summary_length": "medium"
    },
    headers=headers
)

comparison = response.json()

print("Summary Comparison:")
for method, result in comparison["summaries"].items():
    if "error" not in result:
        print(f"\n{method.upper()}:")
        print(f"  Summary: {result['summary'][:200]}...")
        print(f"  Length: {result['summary_length']} chars")
        print(f"  Compression: {result['compression_ratio']:.2%}")

# Visualize comparison
response = requests.post(
    f"{BASE_URL}/export/visualize/summary-comparison",
    json={"summaries": comparison["summaries"]},
    headers=headers
)

chart_data = response.json()
# chart_data['image'] contains base64 encoded image
```

### Example 5: OCR and Information Extraction from Images

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

# Upload image
with open("business_card.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        files=files,
        headers=headers
    )

file_id = response.json()["file_id"]

# Process with OCR
response = requests.get(
    f"{BASE_URL}/documents/{file_id}/process",
    params={
        "use_ocr": True,
        "ocr_engine": "easyocr"  # or "tesseract"
    },
    headers=headers
)

ocr_result = response.json()
extracted_text = ocr_result["result"]["text"]

print("Extracted Text from Image:")
print(extracted_text)

# Extract structured information
response = requests.post(
    f"{BASE_URL}/analysis/extract",
    json={
        "text": extracted_text,
        "extract_persons": True,
        "extract_organizations": True,
        "extract_emails": True,
        "extract_phones": True,
        "extract_addresses": True
    },
    headers=headers
)

info = response.json()

print("\nExtracted Business Card Information:")
if info["persons"]:
    print(f"Name: {info['persons'][0]['name']}")
if info["organizations"]:
    print(f"Company: {info['organizations'][0]['name']}")
if info["emails"]:
    print(f"Email: {info['emails'][0]['email']}")
if info["phone_numbers"]:
    print(f"Phone: {info['phone_numbers'][0]['number']}")
```

### Example 6: Batch Processing Multiple Documents

```python
import requests
import os
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

def process_document(file_path):
    """Process a single document"""
    # Upload
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            headers=headers
        )

    file_id = response.json()["file_id"]

    # Process
    requests.get(
        f"{BASE_URL}/documents/{file_id}/process",
        headers=headers
    )

    # Summarize
    response = requests.post(
        f"{BASE_URL}/summarize/",
        json={
            "file_id": file_id,
            "method": "abstractive",
            "summary_length": "short"
        },
        headers=headers
    )

    summary = response.json()

    return {
        "file": os.path.basename(file_path),
        "file_id": file_id,
        "summary": summary["summary"]
    }

# Process multiple documents in parallel
document_folder = "documents/"
files = [os.path.join(document_folder, f) for f in os.listdir(document_folder)]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_document, files))

# Print results
for result in results:
    print(f"\nFile: {result['file']}")
    print(f"Summary: {result['summary'][:150]}...")
```

### Example 7: Advanced NLP Analysis Pipeline

```python
import requests

BASE_URL = "http://localhost:8000/api"
headers = {"Authorization": f"Bearer {token}"}

text = """
[Your text here...]
"""

# Full NLP analysis
response = requests.post(
    f"{BASE_URL}/analysis/nlp",
    json={
        "text": text,
        "include_entities": True,
        "include_keywords": True,
        "include_pos": True,
        "chunk_size": 512
    },
    headers=headers
)

analysis = response.json()

# Display results
print(f"Document Statistics:")
print(f"  Words: {analysis['word_count']}")
print(f"  Sentences: {analysis['sentence_count']}")
print(f"  Readability (Flesch): {analysis['statistics']['flesch_reading_ease']:.2f}")
print(f"  Grade Level: {analysis['statistics']['flesch_kincaid_grade']:.2f}")

print("\nTop Keywords (YAKE):")
for kw in analysis["keywords"]["yake"][:10]:
    print(f"  - {kw['keyword']} (score: {kw['score']:.4f})")

print("\nNamed Entities:")
for entity_type, entities in analysis["entities"].items():
    print(f"  {entity_type}: {len(entities)} found")
    for entity in entities[:3]:
        print(f"    - {entity['text']}")

# Generate visualizations
# Word cloud
response = requests.post(
    f"{BASE_URL}/export/visualize/wordcloud",
    json={"text": text},
    headers=headers
)
wordcloud = response.json()["image"]

# Entity chart
response = requests.post(
    f"{BASE_URL}/export/visualize/entities",
    json={"entities": analysis["entities"]},
    headers=headers
)
entity_chart = response.json()["image"]

# Keyword chart
response = requests.post(
    f"{BASE_URL}/export/visualize/keywords",
    json={"keywords": analysis["keywords"]["yake"]},
    headers=headers
)
keyword_chart = response.json()["image"]

print("\nVisualizations generated (base64 encoded)")
```

## cURL Examples

### Quick Summary
```bash
curl -X POST "http://localhost:8000/api/summarize/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Your text here...",
    "method": "abstractive",
    "summary_length": "medium"
  }'
```

### Upload and Process
```bash
# Upload
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# Process
curl -X GET "http://localhost:8000/api/documents/FILE_ID/process?use_ocr=false" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Extract Information
```bash
curl -X POST "http://localhost:8000/api/analysis/extract" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Your text...",
    "extract_persons": true,
    "extract_organizations": true,
    "extract_dates": true
  }'
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'http://localhost:8000/api';
let token = '';

async function login() {
  const response = await axios.post(`${BASE_URL}/auth/login`,
    'username=user&password=pass',
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }
  );
  token = response.data.access_token;
}

async function uploadAndSummarize(filePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  // Upload
  const uploadResponse = await axios.post(
    `${BASE_URL}/documents/upload`,
    formData,
    {
      headers: {
        ...formData.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const fileId = uploadResponse.data.file_id;

  // Summarize
  const summaryResponse = await axios.post(
    `${BASE_URL}/summarize/`,
    {
      file_id: fileId,
      method: 'abstractive',
      summary_length: 'medium'
    },
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  return summaryResponse.data;
}

// Usage
(async () => {
  await login();
  const summary = await uploadAndSummarize('document.pdf');
  console.log('Summary:', summary.summary);
})();
```

These examples demonstrate the full capabilities of the platform and can be adapted for various use cases.
