import re
from typing import List, Dict, Any

KNOWN_TEST_PATTERNS = [
    {"name": "Hemoglobin", "pattern": r"hemoglobin\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "g/dL", "ref": "13.0 - 17.0"},
    {"name": "HbA1c", "pattern": r"hba1c\b[:\s]*([\d\.]+)\s*(%)?", "unit": "%", "ref": "4.0 - 5.6"},
    {"name": "Fasting Blood Sugar", "pattern": r"(?:fasting blood sugar|fasting glucose)\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "70 - 99"},
    {"name": "Total Cholesterol", "pattern": r"(?:total cholesterol|cholesterol total)\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "< 200"},
    {"name": "Triglycerides", "pattern": r"triglycerides\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "< 150"},
    {"name": "HDL Cholesterol", "pattern": r"hdl cholesterol\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "> 40"},
    {"name": "LDL Cholesterol", "pattern": r"ldl cholesterol\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "< 100"},
    {"name": "Vitamin D", "pattern": r"(?:vitamin d|25-hydroxy)\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "ng/mL", "ref": "30 - 100"},
    {"name": "Vitamin B12", "pattern": r"vitamin b12\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "pg/mL", "ref": "200 - 900"},
    {"name": "Serum Creatinine", "pattern": r"creatinine\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "0.7 - 1.3"},
    {"name": "Uric Acid", "pattern": r"uric acid\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "mg/dL", "ref": "3.5 - 7.2"},
    {"name": "Platelet Count", "pattern": r"platelet\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "k/uL", "ref": "150 - 450"},
    {"name": "WBC Count", "pattern": r"(?:wbc|white blood cell)\b[:\s]*([\d\.]+)\s*([a-zA-Z/]+)?", "unit": "k/uL", "ref": "4.5 - 11.0"},
]

def extract_lab_observations(text: str) -> List[Dict[str, Any]]:
    """
    Scans text for laboratory test observations and structured test result pairs.
    Preserves numerical values, original text, units, reference ranges, and flags.
    """
    observations = []
    text_lower = text.lower()

    # Pattern-matching extraction
    for test_info in KNOWN_TEST_PATTERNS:
        match = re.search(test_info["pattern"], text_lower, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            try:
                val_num = float(val_str)
            except ValueError:
                val_num = None

            unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else test_info["unit"]
            
            # Simple flagging heuristic based on reference string
            flag = "normal"
            if test_info["name"] == "Hemoglobin" and val_num and val_num < 13.0:
                flag = "low"
            elif test_info["name"] == "Vitamin D" and val_num and val_num < 30.0:
                flag = "low"
            elif test_info["name"] == "Total Cholesterol" and val_num and val_num > 200.0:
                flag = "high"
            elif test_info["name"] == "HbA1c" and val_num and val_num > 5.7:
                flag = "high"

            observations.append({
                "test_name": test_info["name"],
                "value_numeric": val_num,
                "value_text": val_str,
                "unit": unit,
                "reference_range": test_info["ref"],
                "flag": flag,
                "source_page": 1
            })

    # Line-by-line fallback for tabular formats (e.g. "Hemoglobin 11.8 g/dL 13.0-17.0")
    if not observations:
        lines = text.split("\n")
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                # Look for lines with test name, number, unit
                test_candidate = " ".join(parts[:-2])
                val_candidate = parts[-2]
                unit_candidate = parts[-1]
                try:
                    v_num = float(val_candidate)
                    if len(test_candidate) > 2 and len(test_candidate) < 40:
                        observations.append({
                            "test_name": test_candidate.title(),
                            "value_numeric": v_num,
                            "value_text": val_candidate,
                            "unit": unit_candidate,
                            "reference_range": "N/A",
                            "flag": "normal",
                            "source_page": 1
                        })
                except ValueError:
                    pass

    return observations
