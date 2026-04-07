"""
Database models for the recruiting module.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Job(Base):
    """Job posting table"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    required_experience = Column(Integer, default=0)
    required_skill_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="job")


class Candidate(Base):
    """Candidate table"""
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    gender = Column(String(20))  # Male, Female, Other
    experience = Column(Integer, default=0)
    skill_score = Column(Integer, default=0)
    education_level = Column(String(50))  # High School, Bachelor, Master, PhD
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="candidate")


class Application(Base):
    """Application table linking candidates to jobs"""
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    job_id = Column(Integer, ForeignKey('jobs.id'))
    model_score = Column(Float, default=0.0)
    decision = Column(Integer, default=0)  # 0 = rejected, 1 = shortlisted
    reviewed_at = Column(DateTime)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")


# Database setup
DATABASE_URL = "sqlite:///recruiting.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
