"""
Advanced Information Extraction Module
Extracts names, dates, organizations, monetary values, addresses, emails, etc.
"""
import re
from typing import Dict, List, Optional
from datetime import datetime

import spacy
from spacy.matcher import Matcher
import dateparser
from loguru import logger


class InformationExtractor:
    """Extract structured information from text"""

    def __init__(self, spacy_model: str = 'en_core_web_sm'):
        """Initialize information extractor"""
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"spaCy model {spacy_model} not found.")
            self.nlp = spacy.blank('en')

        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()

    def _setup_patterns(self):
        """Setup custom patterns for matching"""
        # Email pattern
        email_pattern = [{"LIKE_EMAIL": True}]
        self.matcher.add("EMAIL", [email_pattern])

        # URL pattern
        url_pattern = [{"LIKE_URL": True}]
        self.matcher.add("URL", [url_pattern])

    def extract_all(self, text: str) -> Dict:
        """
        Extract all information from text

        Args:
            text: Input text

        Returns:
            Dictionary with all extracted information
        """
        doc = self.nlp(text)

        return {
            'persons': self.extract_persons(doc),
            'organizations': self.extract_organizations(doc),
            'locations': self.extract_locations(doc),
            'dates': self.extract_dates(text),
            'monetary_values': self.extract_monetary_values(text),
            'emails': self.extract_emails(text),
            'phone_numbers': self.extract_phone_numbers(text),
            'addresses': self.extract_addresses(text),
            'urls': self.extract_urls(text),
            'legal_references': self.extract_legal_references(text),
            'cybersecurity_indicators': self.extract_cybersecurity_indicators(text),
            'medical_terms': self.extract_medical_terms(doc),
            'custom_entities': self.extract_custom_entities(doc)
        }

    def extract_persons(self, doc) -> List[Dict]:
        """Extract person names"""
        persons = []
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                persons.append({
                    'name': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        return persons

    def extract_organizations(self, doc) -> List[Dict]:
        """Extract organization names"""
        organizations = []
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                organizations.append({
                    'name': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        return organizations

    def extract_locations(self, doc) -> List[Dict]:
        """Extract location names"""
        locations = []
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'FAC']:
                locations.append({
                    'name': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        return locations

    def extract_dates(self, text: str) -> List[Dict]:
        """Extract and parse dates"""
        dates = []

        # Common date patterns
        patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',    # DD Month YYYY
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group()
                parsed_date = dateparser.parse(date_str)

                dates.append({
                    'text': date_str,
                    'parsed': parsed_date.isoformat() if parsed_date else None,
                    'start': match.start(),
                    'end': match.end()
                })

        return dates

    def extract_monetary_values(self, text: str) -> List[Dict]:
        """Extract monetary values"""
        monetary_values = []

        # Patterns for currency
        patterns = [
            r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,000.00
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|CAD|AUD)',  # 1,000.00 USD
            r'(?:USD|EUR|GBP|CAD|AUD)\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # USD 1,000.00
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                monetary_values.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })

        return monetary_values

    def extract_emails(self, text: str) -> List[Dict]:
        """Extract email addresses"""
        emails = []

        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(pattern, text)

        for match in matches:
            emails.append({
                'email': match.group(),
                'start': match.start(),
                'end': match.end()
            })

        return emails

    def extract_phone_numbers(self, text: str) -> List[Dict]:
        """Extract phone numbers"""
        phone_numbers = []

        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                phone_numbers.append({
                    'number': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })

        return phone_numbers

    def extract_addresses(self, text: str) -> List[Dict]:
        """Extract physical addresses"""
        addresses = []

        # Simple pattern for US addresses
        pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir)\.?,?\s+[\w\s]+,?\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?'

        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            addresses.append({
                'address': match.group(),
                'start': match.start(),
                'end': match.end()
            })

        return addresses

    def extract_urls(self, text: str) -> List[Dict]:
        """Extract URLs"""
        urls = []

        pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'

        matches = re.finditer(pattern, text)

        for match in matches:
            urls.append({
                'url': match.group(),
                'start': match.start(),
                'end': match.end()
            })

        return urls

    def extract_legal_references(self, text: str) -> List[Dict]:
        """Extract legal references (case citations, statutes, etc.)"""
        legal_refs = []

        patterns = [
            # Case citations: 123 F.3d 456
            (r'\d+\s+[A-Z]\.(?:\d+d|Supp\.)\s+\d+', 'case_citation'),
            # Statute: 42 U.S.C. § 1983
            (r'\d+\s+U\.S\.C\.\s+§\s*\d+', 'statute'),
            # Section references
            (r'Section\s+\d+(?:\.\d+)*', 'section'),
        ]

        for pattern, ref_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                legal_refs.append({
                    'text': match.group(),
                    'type': ref_type,
                    'start': match.start(),
                    'end': match.end()
                })

        return legal_refs

    def extract_cybersecurity_indicators(self, text: str) -> Dict:
        """Extract cybersecurity-related indicators (IoCs)"""
        indicators = {
            'ip_addresses': [],
            'domain_names': [],
            'file_hashes': [],
            'cve_ids': []
        }

        # IP addresses (IPv4)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        for match in re.finditer(ip_pattern, text):
            ip = match.group()
            # Basic validation
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                indicators['ip_addresses'].append({
                    'ip': ip,
                    'start': match.start(),
                    'end': match.end()
                })

        # Domain names
        domain_pattern = r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'
        for match in re.finditer(domain_pattern, text, re.IGNORECASE):
            indicators['domain_names'].append({
                'domain': match.group(),
                'start': match.start(),
                'end': match.end()
            })

        # File hashes (MD5, SHA1, SHA256)
        hash_patterns = [
            (r'\b[a-fA-F0-9]{32}\b', 'MD5'),
            (r'\b[a-fA-F0-9]{40}\b', 'SHA1'),
            (r'\b[a-fA-F0-9]{64}\b', 'SHA256'),
        ]

        for pattern, hash_type in hash_patterns:
            for match in re.finditer(pattern, text):
                indicators['file_hashes'].append({
                    'hash': match.group(),
                    'type': hash_type,
                    'start': match.start(),
                    'end': match.end()
                })

        # CVE IDs
        cve_pattern = r'\bCVE-\d{4}-\d{4,7}\b'
        for match in re.finditer(cve_pattern, text, re.IGNORECASE):
            indicators['cve_ids'].append({
                'cve_id': match.group().upper(),
                'start': match.start(),
                'end': match.end()
            })

        return indicators

    def extract_medical_terms(self, doc) -> List[Dict]:
        """Extract medical-related entities and terms"""
        medical_terms = []

        # Use spaCy NER for basic medical entities
        medical_labels = ['DISEASE', 'DRUG', 'TREATMENT', 'SYMPTOM']

        for ent in doc.ents:
            # Some medical models use these labels
            if ent.label_ in medical_labels:
                medical_terms.append({
                    'term': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })

        # Common medical term patterns
        medical_patterns = [
            r'\b\d+\s*mg\b',  # Dosage
            r'\b\d+\s*ml\b',
            r'\bICD-(?:9|10)-[A-Z0-9]+\b',  # ICD codes
        ]

        text = doc.text
        for pattern in medical_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                medical_terms.append({
                    'term': match.group(),
                    'type': 'medical_code',
                    'start': match.start(),
                    'end': match.end()
                })

        return medical_terms

    def extract_custom_entities(self, doc) -> Dict:
        """Extract all entities categorized"""
        entities = {}

        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []

            entities[ent.label_].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char
            })

        return entities
