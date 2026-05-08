from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, SessionLocal, PatientDB, UserDB, ReportDB, TestResultDB, TestConfigDB, TestParameterDB, InvoiceDB, AIJobDB, hash_password
from typing import List, Dict, Any
from datetime import datetime
import json

app = FastAPI(title="Pathology Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PatientLoginRequest(BaseModel):
    uhid: str

class StaffLoginRequest(BaseModel):
    username: str
    password: str

class ReportCreationRequest(BaseModel):
    user_id: int
    patient_data: Dict[str, Any]
    test_type: str
    results_data: List[Dict[str, Any]]
    price: float
    discount: float
    paid_amount: float
    payment_mode: str

# ----------------- PATIENT PORTAL ROUTES -----------------

@app.post("/api/patient/login")
def patient_login(req: PatientLoginRequest, db: SessionLocal = Depends(get_db)):
    patient = db.query(PatientDB).filter(PatientDB.uhid == req.uhid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient UHID not found")
    
    return {
        "success": True,
        "patient": {
            "id": patient.id,
            "uhid": patient.uhid,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender
        }
    }

@app.get("/api/patient/{uhid}/reports")
def get_patient_reports(uhid: str, db: SessionLocal = Depends(get_db)):
    patient = db.query(PatientDB).filter(PatientDB.uhid == uhid).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    reports = db.query(ReportDB).filter(
        ReportDB.patient_id == patient.id, 
        ReportDB.status == "Approved"
    ).order_by(ReportDB.created_at.desc()).all()
    
    return [
        {
            "id": rep.id,
            "test_type": rep.test_type,
            "date": rep.created_at.strftime("%Y-%m-%d %H:%M"),
            "status": rep.status,
            "ref_doctor": rep.ref_doctor
        } for rep in reports
    ]

# ----------------- STAFF & DOCTOR ROUTES -----------------

@app.post("/api/staff/login")
def staff_login(req: StaffLoginRequest, db: SessionLocal = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == req.username).first()
    if not user or user.password_hash != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role
        }
    }

@app.post("/api/doctor/login")
def doctor_login(req: StaffLoginRequest, db: SessionLocal = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == req.username).first()
    if not user or user.password_hash != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.role != "Pathologist":
        raise HTTPException(status_code=403, detail="Access denied: Pathologist role required")
        
    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role
        }
    }

@app.get("/api/reports/pending")
def get_pending_reports(db: SessionLocal = Depends(get_db)):
    pending = db.query(ReportDB).filter(ReportDB.status == "Result Entered").order_by(ReportDB.created_at.asc()).all()
    
    return [
        {
            "id": rep.id,
            "patient_name": rep.patient.name,
            "uhid": rep.patient.uhid,
            "test_type": rep.test_type,
            "collection_time": rep.collection_time,
            "status": rep.status
        } for rep in pending
    ]

# ----------------- STAFF DASHBOARD DATA ROUTES -----------------

@app.get("/api/tests")
def get_tests(db: SessionLocal = Depends(get_db)):
    tests = db.query(TestConfigDB).all()
    return [{"name": t.name, "price": t.price} for t in tests]

@app.get("/api/tests/{test_name}/params")
def get_test_params(test_name: str, db: SessionLocal = Depends(get_db)):
    test = db.query(TestConfigDB).filter(TestConfigDB.name == test_name).first()
    if not test:
        return []
    params = db.query(TestParameterDB).filter(TestParameterDB.test_config_id == test.id).all()
    return [{
        "Investigation": p.investigation,
        "Ref_Min": p.ref_min,
        "Ref_Max": p.ref_max,
        "Unit": p.unit
    } for p in params]

@app.post("/api/reports/create")
def create_report(req: ReportCreationRequest, db: SessionLocal = Depends(get_db)):
    try:
        patient = db.query(PatientDB).filter(PatientDB.uhid == req.patient_data.get("uhid")).first()
        if not patient:
            patient = PatientDB(
                uhid=req.patient_data.get("uhid"),
                name=req.patient_data.get("name"),
                age=req.patient_data.get("age"),
                gender=req.patient_data.get("gender")
            )
            db.add(patient)
            db.flush() 
        
        report = ReportDB(
            patient_id=patient.id,
            test_type=req.test_type,
            ref_doctor=req.patient_data.get("ref_doc", "Self"),
            sample_loc=req.patient_data.get("sample_loc", "Main Lab"),
            collection_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            status="Result Entered",
            created_by_id=req.user_id
        )
        db.add(report)
        db.flush()
        
        for res in req.results_data:
            tr = TestResultDB(
                report_id=report.id,
                investigation=res['Investigation'],
                value=float(res['Result']),
                status=res['Status'],
                reference_range=res['Reference Value'],
                unit=res['Unit']
            )
            db.add(tr)
            
        inv_status = "Paid" if (req.paid_amount >= (req.price - req.discount)) else "Partial" if req.paid_amount > 0 else "Unpaid"
        inv = InvoiceDB(
            patient_id=patient.id,
            report_id=report.id,
            total_amount=req.price,
            discount=req.discount,
            paid_amount=req.paid_amount,
            payment_mode=req.payment_mode,
            status=inv_status
        )
        db.add(inv)
        db.flush()
        
        # In a real app we'd call the AI mock here
        ai_job = AIJobDB(
            job_type="REPORT_DRAFT",
            status="REQUIRES_REVIEW",
            target_entity_id=report.id,
            input_payload=json.dumps({"test_type": req.test_type, "results": req.results_data}),
            output_payload=json.dumps({"report_summary": "Auto drafted via API", "needs_manual_review": True})
        )
        db.add(ai_job)
        
        db.commit()
        return {"success": True, "report_id": report.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
