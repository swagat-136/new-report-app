from pydantic import BaseModel, Field
from typing import List

class PatientSchema(BaseModel):
    uhid: str = Field(..., min_length=4, description="Unique Health ID must be at least 4 chars")
    name: str = Field(..., min_length=2, description="Patient Name must be at least 2 chars")
    age: int = Field(..., ge=0, le=120, description="Age must be between 0 and 120")
    gender: str = Field(...)
    ref_doc: str = Field(..., min_length=2, description="Doctor name must be provided")
    sample_loc: str = Field(...)
    collection_time: str
    report_time: str

class TestResultSchema(BaseModel):
    investigation: str
    value: float
    status: str
    reference_range: str
    unit: str

class ReportSchema(BaseModel):
    test_type: str
    patient: PatientSchema
    results: List[TestResultSchema]
