import pandas as pd

def evaluate_result(value: float, ref_min: float, ref_max: float) -> str:
    # Handle critical panic values explicitly
    if value < (ref_min * 0.5):
        return "Critical Low"
    elif value > (ref_max * 1.5):
        return "Critical High"
    elif value < ref_min:
        return "Low"
    elif value > ref_max:
        return "High"
    return "Normal"

def generate_interpretation(df: pd.DataFrame, test_type: str) -> list:
    interpretations = []
    
    for _, row in df.iterrows():
        status = row["Status"]
        investigation = row["Investigation"]
        
        if "High" in status:
            if investigation in ["Creatinine", "Urea"]:
                interpretations.append(f"{status} {investigation} → Kidney dysfunction risk suspected.")
            elif investigation in ["AST (SGOT)", "ALT (SGPT)", "ALP", "Bilirubin (Total)"]:
                interpretations.append(f"{status} {investigation} → Liver stress or damage indicated.")
            elif investigation in ["Total Cholesterol", "LDL Cholesterol", "Triglycerides"]:
                interpretations.append(f"{status} {investigation} → Elevated cardiovascular risk.")
            elif "Blood Sugar" in investigation or "HbA1c" in investigation:
                interpretations.append(f"{status} {investigation} → Hyperglycemia / Diabetes risk.")
            elif investigation in ["Hemoglobin (Hb)", "Total RBC Count"]:
                interpretations.append(f"{status} {investigation} → Possible polycythemia or dehydration.")
            elif investigation == "Total WBC Count":
                interpretations.append(f"{status} {investigation} → Indicates possible infection or inflammation.")
            else:
                interpretations.append(f"{status} {investigation} levels observed.")
                
        elif "Low" in status:
            if "Blood Sugar" in investigation:
                interpretations.append(f"{status} {investigation} → Hypoglycemia risk.")
            elif investigation in ["Hemoglobin (Hb)", "Total RBC Count"]:
                interpretations.append(f"{status} {investigation} → Indicates possible anemia.")
            elif investigation == "Total WBC Count":
                interpretations.append(f"{status} {investigation} → Leukopenia risk.")
            elif investigation == "Platelet Count":
                interpretations.append(f"{status} {investigation} → Thrombocytopenia (low platelets).")
            else:
                interpretations.append(f"{status} {investigation} levels observed.")
                
    if not interpretations:
        return ["All parameters are within normal reference ranges."]
    
    # Deduplicate while preserving order
    seen = set()
    unique_interpretations = [x for x in interpretations if not (x in seen or seen.add(x))]
    return unique_interpretations
