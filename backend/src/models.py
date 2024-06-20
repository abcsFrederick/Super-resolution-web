from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)

#     items = relationship("Item", back_populates="owner")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    job_type = Column(String, index=True)
    # owner_id = Column(Integer, ForeignKey("users.id"))
    slurm_id =  Column(String, index=True)
    status = Column(Integer, index=True)
    log_path =  Column(String, index=True)
    error_path =  Column(String, index=True)
    time = Column(DateTime, index=True)
    # owner = relationship("User", back_populates="items")