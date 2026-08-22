import re
from typing import Dict, Any, Optional
from datetime import datetime

class MedicalExtractor:
    """
    Extracts high-level document metadata: classification type, report date, and clinical highlights.
    """
    
    DOCUMENT_TYPES = {
        "blood_report": ["blood", "hemoglobin", "cbc", "lipid", "cholesterol", "hba1c", "thyroid", "glucose", "serum", "platelet"],
        "prescription": ["prescription", "rx", "medicine", "tablets", "capsule", "dosage", "take 1 tablet", "mg"],
        "mri_report": ["mri", "magnetic resonance", "brain mri", "spine mri"],
        "ct_report": ["ct scan", "computed tomography", "contrast ct"],
        "xray_report": ["x-ray", "xray", "radiograph", "chest x-ray"],
        "pathology_report": ["biopsy", "histopathology", "cytology", "pathology"],
        "discharge_summary": ["discharge summary", "hospitalization", "admission date", "discharge date"],
        "consultation": ["consultation", "doctor notes", "clinical impression", "diagnosis"],
        "insurance_document": ["policy", "insurance claim", "pre-authorization", "claim form", "tpa"],
    }

    def classify_document(self, text: str, filename: str) -> str:
        text_lower = (text + " " + filename).lower()
        
        for doc_type, keywords in self.DOCUMENT_TYPES.items():
            for kw in keywords:
                if kw in text_lower:
                    return doc_type
        return "unknown"

    def extract_document_date(self, text: str) -> Optional[str]:
        # Search for date patterns like YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, Month DD, YYYY
        date_patterns = [
            r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return datetime.now().strftime("%Y-%m-%d")
