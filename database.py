from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import hashlib
from data import REFERENCE_DB

DATABASE_URL = "sqlite:///./pathology.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # "Admin", "Pathologist", "Technician", "Receptionist"
    name = Column(String)

class PatientDB(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    uhid = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    mobile = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reports = relationship("ReportDB", back_populates="patient")

class ReportDB(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    test_type = Column(String)
    ref_doctor = Column(String)
    sample_loc = Column(String)
    collection_time = Column(String)
    report_time = Column(String)
    status = Column(String, default="Registered") # Registered, Result Entered, Approved
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientDB", back_populates="reports")
    results = relationship("TestResultDB", back_populates="report", cascade="all, delete-orphan")
    creator = relationship("UserDB", foreign_keys=[created_by_id])
    approver = relationship("UserDB", foreign_keys=[approved_by_id])

class TestResultDB(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    investigation = Column(String)
    value = Column(Float)
    status = Column(String)
    reference_range = Column(String)
    unit = Column(String)
    report = relationship("ReportDB", back_populates="results")

class AIJobDB(Base):
    __tablename__ = "ai_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String) # 'REPORT_DRAFT', 'OCR_EXTRACTION', 'ANALYTICS'
    status = Column(String, default="PENDING") # 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REQUIRES_REVIEW'
    target_entity_id = Column(Integer) # e.g., Report ID or Document ID
    input_payload = Column(String) # Raw data sent to AI (JSON string)
    output_payload = Column(String) # AI structured response (JSON string)
    human_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class DocumentDB(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True) # Could be null if patient unknown
    file_path = Column(String)
    doc_type = Column(String) # 'PRESCRIPTION', 'LEGACY_REPORT'
    extracted_data = Column(String) # Populated by IDP Module (JSON string)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatContextDB(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer) # Patient or Staff ID
    session_id = Column(String)
    message = Column(String)
    role = Column(String) # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)
    
class TestConfigDB(Base):
    __tablename__ = "test_configs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price = Column(Float, default=500.0)
    parameters = relationship("TestParameterDB", back_populates="test_config", cascade="all, delete-orphan")

class TestParameterDB(Base):
    __tablename__ = "test_parameters"
    id = Column(Integer, primary_key=True, index=True)
    test_config_id = Column(Integer, ForeignKey("test_configs.id"))
    investigation = Column(String)
    ref_min = Column(Float)
    ref_max = Column(Float)
    unit = Column(String)
    type = Column(String, default="numeric")
    test_config = relationship("TestConfigDB", back_populates="parameters")

class InvoiceDB(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))
    total_amount = Column(Float)
    discount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    payment_mode = Column(String, nullable=True) # Cash, UPI, Card
    status = Column(String, default="Unpaid") # Unpaid, Partial, Paid
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientDB")
    report = relationship("ReportDB")

class AuditLogDB(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)
    entity_type = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed users if empty
        if db.query(UserDB).count() == 0:
            users = [
                UserDB(username="admin", password_hash=hash_password("admin123"), role="Admin", name="System Admin"),
                UserDB(username="patho", password_hash=hash_password("patho123"), role="Pathologist", name="Dr. Bimala Mishra"),
                UserDB(username="tech", password_hash=hash_password("tech123"), role="Technician", name="Lab Tech 1"),
                UserDB(username="reception", password_hash=hash_password("rec123"), role="Receptionist", name="Front Desk")
            ]
            db.add_all(users)
            db.commit()

        # Seed initial test data if empty
        if db.query(TestConfigDB).count() == 0:
            for test_name, params in REFERENCE_DB.items():
                price = 300.0 if "Sugar" in test_name else 600.0
                test_config = TestConfigDB(name=test_name, price=price)
                db.add(test_config)
                db.flush()
                for param in params:
                    test_param = TestParameterDB(
                        test_config_id=test_config.id,
                        investigation=param["Investigation"],
                        ref_min=param["Ref_Min"],
                        ref_max=param["Ref_Max"],
                        unit=param["Unit"],
                        type=param.get("Type", "numeric")
                    )
                    db.add(test_param)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding DB: {e}")
    finally:
        db.close()
