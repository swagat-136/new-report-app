def get_reference_data():
    return {
        "KFT": [
            {"Investigation": "Urea", "Ref_Min": 13.0, "Ref_Max": 43.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Creatinine", "Ref_Min": 0.7, "Ref_Max": 1.3, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Uric Acid", "Ref_Min": 3.5, "Ref_Max": 7.2, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Sodium", "Ref_Min": 136.0, "Ref_Max": 145.0, "Unit": "mEq/L", "Type": "numeric"},
            {"Investigation": "Potassium", "Ref_Min": 3.5, "Ref_Max": 5.1, "Unit": "mEq/L", "Type": "numeric"}
        ],
        "LFT": [
            {"Investigation": "AST (SGOT)", "Ref_Min": 8.0, "Ref_Max": 48.0, "Unit": "U/L", "Type": "numeric"},
            {"Investigation": "ALT (SGPT)", "Ref_Min": 7.0, "Ref_Max": 55.0, "Unit": "U/L", "Type": "numeric"},
            {"Investigation": "ALP", "Ref_Min": 40.0, "Ref_Max": 129.0, "Unit": "U/L", "Type": "numeric"},
            {"Investigation": "Bilirubin (Total)", "Ref_Min": 0.1, "Ref_Max": 1.2, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Protein (Total)", "Ref_Min": 6.0, "Ref_Max": 8.3, "Unit": "g/dL", "Type": "numeric"}
        ],
        "Lipid Profile": [
            {"Investigation": "Total Cholesterol", "Ref_Min": 0.0, "Ref_Max": 199.9, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "HDL Cholesterol", "Ref_Min": 40.0, "Ref_Max": 100.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "LDL Cholesterol", "Ref_Min": 0.0, "Ref_Max": 99.9, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "VLDL", "Ref_Min": 2.0, "Ref_Max": 30.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Triglycerides", "Ref_Min": 0.0, "Ref_Max": 149.9, "Unit": "mg/dL", "Type": "numeric"}
        ],
        "Blood Sugar": [
            {"Investigation": "Fasting Blood Sugar (FBS)", "Ref_Min": 70.0, "Ref_Max": 100.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Postprandial Blood Sugar (PPBS)", "Ref_Min": 70.0, "Ref_Max": 140.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "Random Blood Sugar (RBS)", "Ref_Min": 70.0, "Ref_Max": 140.0, "Unit": "mg/dL", "Type": "numeric"},
            {"Investigation": "HbA1c", "Ref_Min": 4.0, "Ref_Max": 5.6, "Unit": "%", "Type": "numeric"}
        ],
        "CBC": [
            {"Investigation": "Hemoglobin (Hb)", "Ref_Min": 13.0, "Ref_Max": 17.0, "Unit": "g/dL", "Type": "numeric"},
            {"Investigation": "Total RBC Count", "Ref_Min": 4.5, "Ref_Max": 5.5, "Unit": "mill/cumm", "Type": "numeric"},
            {"Investigation": "Total WBC Count", "Ref_Min": 4000.0, "Ref_Max": 11000.0, "Unit": "cells/cumm", "Type": "numeric"},
            {"Investigation": "Platelet Count", "Ref_Min": 1.5, "Ref_Max": 4.5, "Unit": "lakhs/cumm", "Type": "numeric"},
            {"Investigation": "Neutrophils", "Ref_Min": 40.0, "Ref_Max": 75.0, "Unit": "%", "Type": "numeric"},
            {"Investigation": "Lymphocytes", "Ref_Min": 20.0, "Ref_Max": 45.0, "Unit": "%", "Type": "numeric"},
            {"Investigation": "Eosinophils", "Ref_Min": 1.0, "Ref_Max": 6.0, "Unit": "%", "Type": "numeric"},
            {"Investigation": "Monocytes", "Ref_Min": 2.0, "Ref_Max": 10.0, "Unit": "%", "Type": "numeric"},
            {"Investigation": "Basophils", "Ref_Min": 0.0, "Ref_Max": 2.0, "Unit": "%", "Type": "numeric"}
        ]
    }

REFERENCE_DB = get_reference_data()
