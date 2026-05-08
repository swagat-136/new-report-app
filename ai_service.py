import json
from datetime import datetime

def generate_ai_report_draft(test_type, results_data):
    """
    Mock implementation of an LLM call.
    In a real system, this would call OpenAI/Gemini with the system prompt 
    and parse the resulting JSON.
    """
    abnormal = [r for r in results_data if r['Status'] not in ['Normal', '']]
    
    if not abnormal:
        report_summary = f"The {test_type} results are entirely within normal physiological reference ranges. No significant clinical abnormalities detected."
        patient_summary = f"Great news! Your {test_type} results are completely normal and show no signs of concern."
        needs_review = False
        reasons = []
    else:
        abnormal_names = ", ".join([a['Investigation'] for a in abnormal])
        report_summary = f"The {test_type} panel reveals abnormal values for {abnormal_names}. Clinical correlation is required to rule out underlying pathology."
        patient_summary = f"Your {test_type} results show that {abnormal_names} are outside the normal range. Please discuss these specific markers with your referring doctor."
        needs_review = True
        reasons = ["Abnormal values detected requiring clinical verification."]

    output = {
      "report_summary": report_summary,
      "abnormal_flags": abnormal,
      "patient_friendly_summary": patient_summary,
      "needs_manual_review": needs_review,
      "review_reasons": reasons
    }
    
    return json.dumps(output)

def extract_data_from_document(file_path, doc_type):
    """
    Mock IDP (Intelligent Document Processing).
    In production, this would call AWS Textract or Google Document AI.
    Returns structured JSON of extracted info.
    """
    # Mocking standard extraction
    extracted = {
        "confidence_score": 0.92,
        "patient_name": "Unknown",
        "uhid_found": "",
        "requested_tests": [],
        "referring_doctor": "Dr. Unspecified",
        "collection_date": datetime.now().strftime("%Y-%m-%d"),
        "raw_text_snippet": "Extracted text block from OCR..."
    }
    
    if doc_type == "PRESCRIPTION":
        extracted["patient_name"] = "Sample Patient (OCR)"
        extracted["requested_tests"] = ["CBC", "Lipid Profile"]
        extracted["referring_doctor"] = "Dr. A. Smith"
        extracted["raw_text_snippet"] = "Rx: CBC, Lipid Panel. Dx: Hypertension screening."
        
    elif doc_type == "LEGACY_REPORT":
        extracted["patient_name"] = "Sample Patient (OCR)"
        extracted["uhid_found"] = "UHID-999999"
        extracted["requested_tests"] = ["LFT"]
        extracted["raw_text_snippet"] = "AST: 45, ALT: 50, Bilirubin: 0.9"
        
    return json.dumps(extracted)

def chat_with_patient_bot(message, patient_name, pending_reports):
    """
    Mock Patient Support Chatbot.
    System prompt enforces: Answer FAQs on report download, test prep. Do not diagnose.
    """
    msg = message.lower()
    if "when" in msg or "ready" in msg or "time" in msg:
        if pending_reports:
            return f"Hello {patient_name}, you currently have pending reports. Most tests take 4-6 hours to be reviewed by our pathologist. You will be able to download them here once approved."
        else:
            return f"Hello {patient_name}, you don't have any pending reports. If you recently gave a sample, it might not be registered in the system yet."
    elif "fast" in msg or "eat" in msg or "water" in msg:
        return "For fasting tests like Fasting Blood Sugar or Lipid Profile, please ensure a 10-12 hour overnight fast. Drinking plain water is allowed."
    elif "mean" in msg or "high" in msg or "low" in msg or "diagnose" in msg:
        return "I am a lab support assistant and cannot provide medical diagnoses or interpret your results. Please share your downloaded report with your referring doctor for clinical advice."
    else:
        return "I can help with questions about lab timings, report availability, and test preparations. How can I assist you today?"

def chat_with_staff_rag(message):
    """
    Mock Staff Knowledge Assistant (RAG).
    In production, this queries a Vector DB (like Pinecone/Qdrant) loaded with SOPs.
    """
    msg = message.lower()
    if "lipemia" in msg or "hemolyzed" in msg or "sample" in msg:
        return "According to SOP-LAB-002: If a sample is grossly hemolyzed or lipemic, reject the sample and request a redraw. Document the rejection in the LIS."
    elif "price" in msg or "cost" in msg or "discount" in msg:
        return "Based on the latest pricing catalog, standard discount limits for Receptionists are capped at 10%. Any discount above 10% requires Admin override."
    elif "turnaround" in msg or "tat" in msg:
        return "Routine Biochemistry TAT is 4 hours. Microbiology cultures TAT is 48-72 hours. Urgent/STAT samples must be processed within 1 hour."
    else:
        return "I am the Staff Knowledge Assistant. I can answer questions based on our internal SOPs, pricing catalogs, and lab policies. What do you need to know?"

def generate_smart_triage_alerts(pending_reports_data):
    """
    Mock Smart Triage AI.
    Analyzes pending reports and flags critical priorities.
    """
    alerts = []
    for rep in pending_reports_data:
        # Mocking an AI heuristic
        if rep.get("has_critical"):
            alerts.append({"level": "CRITICAL", "message": f"Report #{rep['id']} ({rep['test_type']}) contains critical panic values requiring immediate Pathologist review."})
        elif "CBC" in rep['test_type']:
            alerts.append({"level": "WARNING", "message": f"Report #{rep['id']} (CBC) has been pending. Review manual inputs for accuracy."})
            
    if not alerts:
        alerts.append({"level": "INFO", "message": "All pending workloads are within standard operational SLAs."})
        
    return alerts

def generate_analytics_insights(metrics):
    """
    Mock Analytics Copilot.
    Generates natural language insights based on raw SQL metrics.
    """
    total_rev = metrics.get('total_revenue', 0)
    total_reports = metrics.get('total_reports', 0)
    
    insights = [
        f"Based on current data, your lab has processed {total_reports} tests. Revenue generation is tracking well.",
        "Anomaly Trend: We noticed a slight 5% increase in elevated Liver Function Tests this week compared to last month.",
        "Turnaround Time (TAT) Optimization: 95% of reports are approved within the 4-hour SLA. Great job!",
        "Recommendation: Consider offering a bundled 'Comprehensive Health Check' package, as CBC and LFT are frequently requested separately."
    ]
    return insights
