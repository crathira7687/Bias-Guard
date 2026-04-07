"""
BiasGuard Recruiting Server
FastAPI-based recruiting module that integrates with BiasGuard bias auditing.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import BiasGuard modules
from recruiting.models import Job, Candidate, Application, init_db, get_db
from recruiting.scoring import score_candidate

# Create FastAPI app
app = FastAPI(title="BiasGuard Recruiting", description="Minimal recruiting software with bias auditing")

# Templates
templates = Jinja2Templates(directory="recruiting/templates")


# ============================================================================
# AUDIT HOOK - Integration with existing BiasGuard
# ============================================================================

def call_bias_guard_audit(job_id: int, candidate_id: int, gender: str, decision: int, model_score: float):
    """
    Call existing BiasGuard audit function after every decision.
    This ensures recruiting system feeds bias monitor.
    """
    audit_data = {
        'job_id': job_id,
        'candidate_id': candidate_id,
        'gender': gender,
        'decision': decision,
        'model_score': model_score
    }
    
    # Log the audit data
    print(f"[AUDIT] BiasGuard audit hook called: {audit_data}")
    
    # TODO: In production, integrate with actual BiasGuard API
    # from app import BiasAnalyzer
    # analyzer = BiasAnalyzer()
    # analyzer.audit(audit_data)
    
    return audit_data


# ============================================================================
# HOME AND NAVIGATION
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("home.html", {"request": request})


# ============================================================================
# JOB POSTING MODULE
# ============================================================================

@app.get("/jobs/create", response_class=HTMLResponse)
async def create_job_page(request: Request):
    """Show job creation form"""
    return templates.TemplateResponse("create_job.html", {"request": request})


@app.post("/jobs/create")
async def create_job(
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


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show job details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job": job
    })


@app.get("/jobs", response_class=HTMLResponse)
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

@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_page(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show application form"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return templates.TemplateResponse("apply.html", {
        "request": request,
        "job": job
    })


@app.post("/apply/{job_id}")
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
    from datetime import datetime
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


@app.get("/application/{app_id}", response_class=HTMLResponse)
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

@app.get("/recruiter/review/{job_id}", response_class=HTMLResponse)
async def review_applications(
    request: Request,
    job_id: int,
    blind: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Review applications in blind or non-blind mode"""
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

@app.get("/recruiter/dashboard", response_class=HTMLResponse)
async def recruiter_dashboard_index(request: Request, db: Session = Depends(get_db)):
    """Show main dashboard with all jobs overview"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    
    # Get overall stats
    all_apps = db.query(Application).all()
    total_applicants = len(all_apps)
    shortlisted = sum(1 for app in all_apps if app.decision == 1)
    rejected = total_applicants - shortlisted
    
    # Jobs with stats
    jobs_data = []
    for job in jobs:
        apps = [a for a in all_apps if a.job_id == job.id]
        job_shortlisted = sum(1 for a in apps if a.decision == 1)
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'total_applicants': len(apps),
            'shortlisted': job_shortlisted,
            'selection_rate': round(job_shortlisted / len(apps) * 100, 1) if apps else 0
        })
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "job": None,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "selection_rate": round(shortlisted / total_applicants * 100, 1) if total_applicants > 0 else 0,
        "gender_stats": {},
        "jobs": jobs_data
    })


@app.get("/recruiter/dashboard/{job_id}", response_class=HTMLResponse)
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
# API ROUTES (JSON)
# ============================================================================

@app.post("/api/jobs", status_code=201)
async def api_create_job(job: Job, db: Session = Depends(get_db)):
    """API endpoint to create a job"""
    new_job = Job(
        title=job.title,
        description=job.description,
        required_experience=job.required_experience,
        required_skill_score=job.required_skill_score
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return {"id": new_job.id, "title": new_job.title, "status": "created"}


@app.get("/api/jobs")
async def api_list_jobs(db: Session = Depends(get_db)):
    """API endpoint to list all jobs"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [{"id": j.id, "title": j.title, "description": j.description} for j in jobs]


@app.post("/api/apply")
async def api_apply(job_id: int, candidate: Candidate, db: Session = Depends(get_db)):
    """API endpoint to submit application"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create candidate
    from datetime import datetime
    new_candidate = Candidate(
        name=candidate.name,
        gender=candidate.gender,
        experience=candidate.experience,
        skill_score=candidate.skill_score,
        education_level=candidate.education_level
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    # Score the candidate
    candidate_data = {
        'skill_score': candidate.skill_score,
        'experience': candidate.experience,
        'education_level': candidate.education_level
    }
    job_data = {
        'required_skill_score': job.required_skill_score,
        'required_experience': job.required_experience
    }
    
    result = score_candidate(candidate_data, job_data)
    
    # Create application
    application = Application(
        candidate_id=new_candidate.id,
        job_id=job_id,
        model_score=result['model_score'],
        decision=result['decision'],
        reviewed_at=datetime.utcnow()
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Call BiasGuard audit hook
    audit_data = call_bias_guard_audit(
        job_id=job_id,
        candidate_id=new_candidate.id,
        gender=candidate.gender,
        decision=result['decision'],
        model_score=result['model_score']
    )
    
    return {
        "application_id": application.id,
        "candidate_id": new_candidate.id,
        "model_score": result['model_score'],
        "decision": result['decision'],
        "decision_text": "Shortlisted" if result['decision'] == 1 else "Not Selected",
        "bias_audit": audit_data
    }


# ============================================================================
# INITIALIZE DATABASE ON STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
