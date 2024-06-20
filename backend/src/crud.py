from sqlalchemy.orm import Session

from . import models, schemas


# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).offset(skip).limit(limit).all()

def get_job_by_id(db: Session, slurm_id: int):
    return db.query(models.Job).filter(models.Job.slurm_id == slurm_id).first()

def create_job(db: Session, job: schemas.JobCreate): #, user_id: int):
    db_job = models.Job(**job.dict())#, owner_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(db: Session, slurm_id: str, value: dict):
    job = db.query(models.Job).filter(models.Job.slurm_id == slurm_id)
    job.update(value)
    db.commit()
    return job

def delete_job(db: Session, id: int):
    job = db.query(models.Job).filter(models.Job.id == id)
    job.delete()
    db.commit()
    return job

def delete_jobs_by_type(db: Session, job_type: str):
    job = db.query(models.Job).filter(models.Job.job_type == job_type)
    job.delete()
    db.commit()
    return job