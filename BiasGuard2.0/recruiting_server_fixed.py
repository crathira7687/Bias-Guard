"""
BiasGuard Recruiting Server - Fixed Version
FastAPI-based recruiting module that integrates with BiasGuard bias auditing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from recruiting.models import Job, Candidate, Application, init_db, get_db
from recruiting.scoring import score_candidate

app = FastAPI(title="BiasGuard Recruiting", description="Minimal recruiting software with bias auditing")
templates = Jinja2Templates(directory="recruiting/templates")

# Pydantic models for API
class JobCreate(BaseModel):
    title: str
    description: str = ""
    required_experience: int = 0
    required_skill_score: int = 0

class CandidateCreate(BaseModel):
    name: str
    gender: str
    experience: int
    skill_score: int
    education_level: str


def call_bias_guard_audit(job_id: int, candidate_id: int, gender: str, decision: int, model_score: float):
    """Audit hook - logs every hiring decision for bias monitoring."""
    audit_data = {
        'job_id': job_id,
        'candidate_id': candidate_id,
        'gender': gender,
        'decision': decision,
        'model_score': model_score
    }
    print(f"[AUDIT] BiasGuard audit hook called: {audit_data}")
    return audit_data


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/jobs/create", response_class=HTMLResponse)
async def create_job_page(request: Request):
    return templates.TemplateResponse("create_job.html", {"request": request})


@app.post("/jobs/create")
async def create_job(
    title: str = Form(...),
    description: str = Form(""),
    required_experience: int = Form(0),
    required_skill_score: int = Form(0),
    db: Session = Depends(get_db)
):
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
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})


@app.get("/jobs", response_class=HTMLResponse)
async def list_jobs(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return templates.TemplateResponse("list_jobs.html", {"request": request, "jobs": jobs})


@app.get("/apply/{job_id}", response_class=HTMLResponse)
async def apply_page(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("apply.html", {"request": request, "job": job})


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
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    
    result = score_candidate(
        {'skill_score': skill_score, 'experience': experience, 'education_level': education_level},
        {'required_skill_score': job.required_skill_score, 'required_experience': job.required_experience}
    )
    
    application = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        model_score=result['model_score'],
        decision=result['decision'],
        reviewed_at=datetime.utcnow()
    )
    db.add(application)
    db.commit()
    
    call_bias_guard_audit(job_id, candidate.id, gender, result['decision'], result['model_score'])
    
    return RedirectResponse(url=f"/application/{application.id}?submitted=true", status_code=303)


@app.get("/application/{app_id}", response_class=HTMLResponse)
async def application_result(
    request: Request,
    app_id: int,
    submitted: bool = False,
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return templates.TemplateResponse(
        "application_result.html",
        {"request": request, "application": app, "submitted": submitted}
    )


@app.get("/recruiter/review/{job_id}", response_class=HTMLResponse)
async def review_applications(
    request: Request,
    job_id: int,
    blind: bool = Query(True),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    return templates.TemplateResponse(
        "review.html",
        {"request": request, "job": job, "applications": applications, "blind": blind}
    )


@app.get("/recruiter/dashboard", response_class=HTMLResponse)
async def recruiter_dashboard_index(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    all_apps = db.query(Application).all()
    total_applicants = len(all_apps)
    shortlisted = sum(1 for app in all_apps if app.decision == 1)
    
    jobs_data = []
    for j in jobs:
        apps_for_job = [a for a in all_apps if a.job_id == j.id]
        job_shortlisted = sum(1 for a in apps_for_job if a.decision == 1)
        jobs_data.append({
            'id': j.id,
            'title': j.title,
            'total_applicants': len(apps_for_job),
            'shortlisted': job_shortlisted
        })
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "job": None,
            "total_applicants": total_applicants,
            "shortlisted": shortlisted,
            "rejected": total_applicants - shortlisted,
            "selection_rate": round(shortlisted / total_applicants * 100, 1) if total_applicants else 0,
            "gender_stats": {},
            "jobs": jobs_data
        }
    )


@app.get("/recruiter/dashboard/{job_id}", response_class=HTMLResponse)
async def recruiter_dashboard(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    applications = db.query(Application).filter(Application.job_id == job_id).all()
    total = len(applications)
    shortlisted = sum(1 for app in applications if app.decision == 1)
    
    gender_stats = {}
    for app in applications:
        g = app.candidate.gender
        if g not in gender_stats:
            gender_stats[g] = {'total': 0, 'shortlisted': 0}
        gender_stats[g]['total'] += 1
        if app.decision == 1:
            gender_stats[g]['shortlisted'] += 1
    
    for g in gender_stats:
        gender_stats[g]['rate'] = round(
            gender_stats[g]['shortlisted'] / gender_stats[g]['total'] * 100, 1
        ) if gender_stats[g]['total'] else 0
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "job": job,
            "total_applicants": total,
            "shortlisted": shortlisted,
            "rejected": total - shortlisted,
            "selection_rate": round(shortlisted / total * 100, 1) if total else 0,
            "gender_stats": gender_stats
        }
    )


# API Routes
@app.post("/api/jobs", status_code=201)
async def api_create_job(job: JobCreate, db: Session = Depends(get_db)):
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
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [{"id": j.id, "title": j.title, "description": j.description} for j in jobs]


@app.post("/api/apply")
async def api_apply(job_id: int, candidate: CandidateCreate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    
    result = score_candidate(
        {
            'skill_score': candidate.skill_score,
            'experience': candidate.experience,
            'education_level': candidate.education_level
        },
        {
            'required_skill_score': job.required_skill_score,
            'required_experience': job.required_experience
        }
    )
    
    application = Application(
        candidate_id=new_candidate.id,
        job_id=job_id,
        model_score=result['model_score'],
        decision=result['decision'],
        reviewed_at=datetime.utcnow()
    )
    db.add(application)
    db.commit()
    
    audit_data = call_bias_guard_audit(
        job_id,
        new_candidate.id,
        candidate.gender,
        result['decision'],
        result['model_score']
    )
    
    return {
        "application_id": application.id,
        "candidate_id": new_candidate.id,
        "model_score": result['model_score'],
        "decision": result['decision'],
        "decision_text": "Shortlisted" if result['decision'] == 1 else "Not Selected",
        "bias_audit": audit_data
    }


@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
