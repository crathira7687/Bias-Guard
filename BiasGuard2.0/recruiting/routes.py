"""
Routes for the recruiting module.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from recruiting.models import Job, Candidate, Application, get_db, init_db
from recruiting.scoring import score_candidate

# Create router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="recruiting/templates")


# ============================================================================
# AUDIT HOOK - Integration with BiasGuard
# ============================================================================

def call_bias_guard_audit(job_id: int, candidate_id: int, gender: str, decision: int, model_score: float):
    """
    Call existing BiasGuard audit function after every decision.
    This ensures recruiting system feeds bias monitor.
    
    Args:
        job_id: The job ID
        candidate_id: The candidate ID
        gender: Candidate's gender
        decision: The hiring decision (0 or 1)
        model_score: The model score
    """
    audit_data = {
        'job_id': job_id,
        'candidate_id': candidate_id,
        'gender': gender,
        'decision': decision,
        'model_score': model_score
    }
    
    # Log the audit data (in production, this would call the actual BiasGuard API)
    print(f"[AUDIT] BiasGuard audit hook called: {audit_data}")
    
    # TODO: Integrate with actual BiasGuard audit function
    # bias_guard_client.audit_decision(audit_data)
    
    return audit_data


# ============================================================================
# JOB POSTING MODULE
# ============================================================================

@router.get("/jobs/create", response_class=HTMLResponse)
async def create_job_page(request: Request):
    """Show job creation form"""
    return templates.TemplateResponse("create_job.html", {"request": request})


@router.post("/jobs/create")
async def create_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    required_experience: int = Form(0),
    required_skill_score: int = Form(0),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    job = Job(
        title=title,
        description=description,
        required_experience=required_experience,
        required_skill_score=required_skill_score
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show job details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job": job
    })


@router.get("/jobs", response_class=HTMLResponse)
async def list_jobs(request: Request, db: Session = Depends(get_db)):
    """List all jobs"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return templates.TemplateResponse("list_jobs.html", {
        "request": request,
        "jobs": jobs
    })


# ============================================================================
# CANDIDATE APPLICATION MODULE
# ============================================================================

@router.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_page(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show application form"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse("apply.html", {
        "request": request,
        "job": job
    })


@router.post("/apply/{job_id}")
async def apply_for_job(
    job_id: int,
    name: str = Form(...),
    gender: str = Form(...),
    experience: int = Form(...),
    skill_score: int = Form(...),
    education_level: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit job application"""
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create candidate
    candidate = Candidate(
        name=name,
        gender=gender,
        experience=experience,
        skill_score=skill_score,
        education_level=education_level
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    # Score the candidate using the scoring model
    candidate_data = {
        'skill_score': skill_score,
        'experience': experience,
        'education_level': education_level
    }
    job_data = {
        'required_skill_score': job.required_skill_score,
        'required_experience': job.required_experience
    }
    
    result = score_candidate(candidate_data, job_data)
    
    # Create application with decision
    application = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        model_score=result['model_score'],
        decision=result['decision'],
        reviewed_at=datetime.utcnow()
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Call BiasGuard audit hook
    call_bias_guard_audit(
        job_id=job_id,
        candidate_id=candidate.id,
        gender=gender,
        decision=result['decision'],
        model_score=result['model_score']
    )
    
    return RedirectResponse(url=f"/application/{application.id}?submitted=true", status_code=303)


@router.get("/application/{app_id}", response_class=HTMLResponse)
async def application_result(request: Request, app_id: int, submitted: bool = False, db: Session = Depends(get_db)):
    """Show application result"""
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return templates.TemplateResponse("application_result.html", {
        "request": request,
        "application": app,
        "submitted": submitted
    })


# ============================================================================
# BLIND REVIEW MODE
# ============================================================================

@router.get("/recruiter/review/{job_id}", response_class=HTMLResponse)
async def review_applications(
    request: Request,
    job_id: int,
    blind: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Review applications in blind or non-blind mode.
    
    Args:
        job_id: The job ID to review
        blind: If True, hide name and gender (default True)
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    
    return templates.TemplateResponse("review.html", {
        "request": request,
        "job": job,
        "applications": applications,
        "blind": blind
    })


# ============================================================================
# RECRUITER DASHBOARD
# ============================================================================

@router.get("/recruiter/dashboard/{job_id}", response_class=HTMLResponse)
async def recruiter_dashboard(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show recruiter dashboard with statistics"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get all applications for this job
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    
    total_applicants = len(applications)
    shortlisted = sum(1 for app in applications if app.decision == 1)
    rejected = total_applicants - shortlisted
    selection_rate = (shortlisted / total_applicants * 100) if total_applicants > 0 else 0
    
    # Get candidates with their applications
    shortlisted_by_gender = {}
    for app in applications:
        gender = app.candidate.gender
        if gender not in shortlisted_by_gender:
            shortlisted_by_gender[gender] = {'total': 0, 'shortlisted': 0}
        shortlisted_by_gender[gender]['total'] += 1
        if app.decision == 1:
            shortlisted_by_gender[gender]['shortlisted'] += 1
    
    # Calculate selection rate by gender
    gender_stats = {}
    for gender, stats in shortlisted_by_gender.items():
        gender_stats[gender] = {
            'total': stats['total'],
            'shortlisted': stats['shortlisted'],
            'rate': (stats['shortlisted'] / stats['total'] * 100) if stats['total'] > 0 else 0
        }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "job": job,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "selection_rate": round(selection_rate, 1),
        "gender_stats": gender_stats
    })


# ============================================================================
# INIT DATABASE
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
