import re
from typing import List, Dict, Any

COMMON_MED_REGEX = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(\d+\s*(?:mg|mcg|g|ml|IU|units))\b'
PRESCRIPTION_KEYWORDS = ["tablet", "capsule", "syrup", "injection", "once daily", "twice daily", "bd", "od", "tds", "stat", "po"]

def extract_medications(text: str) -> List[Dict[str, Any]]:
    """
    Extracts structured medication records from prescriptions or consultation notes.
    Returns list of medication records.
    """
    medications = []
    
    # 1. Match common pattern like "Atorvastatin 10 mg" or "Metformin 500mg"
    matches = re.findall(COMMON_MED_REGEX, text)
    for med_name, dosage in matches:
        # Filter out common non-medicine words
        if med_name.lower() in ["total cholesterol", "vitamin d", "fasting blood", "serum creatinine", "page", "patient"]:
            continue
            
        medications.append({
            "medicine_name": med_name.strip(),
            "dosage": dosage.strip(),
            "frequency": "Once daily", # Default inferred or extracted
            "status": "active",
            "source_page": 1
        })

    # 2. Line-by-line fallback for prescription lists containing keywords
    if not medications:
        for line in text.split("\n"):
            line_str = line.strip()
            if any(kw in line_str.lower() for kw in PRESCRIPTION_KEYWORDS):
                parts = line_str.split("-")
                name = parts[0].strip()
                dosage = parts[1].strip() if len(parts) > 1 else "As directed"
                if len(name) > 2 and len(name) < 50:
                    medications.append({
                        "medicine_name": name,
                        "dosage": dosage,
                        "frequency": "As directed",
                        "status": "active",
                        "source_page": 1
                    })

    return medications
