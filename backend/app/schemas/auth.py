"""Pydantic schemas for User Authentication and Trainee Diagnostic Performance."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class LoginRequest(BaseModel):
    """User authentication request."""
    email: str = Field(..., description="User login email (e.g. TR-8041@ggmail.com or supervisor@ggmail.com)")
    password: Optional[str] = Field(default="", description="User password")
    role: Optional[str] = Field(default=None, description="Explicit role selection: 'trainee' or 'supervisor'")


class UserProfile(BaseModel):
    """Authenticated user profile."""
    email: str
    role: str = Field(..., description="'trainee' or 'supervisor'")
    user_id: str
    display_name: str
    permissions: List[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    """Authentication response with user session."""
    success: bool
    user: UserProfile
    message: str


class TraineeDiagnosisSubmission(BaseModel):
    """Diagnostic submission made by a trainee for a synthetic patient avatar."""
    patient_id: str
    trainee_id: str
    trainee_email: str
    primary_diagnosis: str
    differential_diagnoses: List[str] = Field(default_factory=list)
    clinical_justification: str = ""
    months_elapsed: int = 0
    ordered_investigations: List[str] = Field(default_factory=list)


class TraineeDiagnosisEvaluation(BaseModel):
    """Evaluation result for a trainee diagnostic submission."""
    submission_id: str
    patient_id: str
    trainee_id: str
    trainee_email: str
    primary_diagnosis: str
    ground_truth_disease_id: str
    ground_truth_disease_name: str
    is_correct: bool
    accuracy_score: float = Field(..., description="0 to 100 percentage score")
    efficiency_score: float = Field(..., description="Test ordering efficiency score")
    hallmarks_detected: List[str] = Field(default_factory=list)
    missed_hallmarks: List[str] = Field(default_factory=list)
    supervisor_debriefing: str
    submitted_at_utc: str
