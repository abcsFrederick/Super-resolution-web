from datetime import datetime
from typing import Union

from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    description: Union[str, None] = None
    job_type: str
    slurm_id: str
    status: int
    log_path: str
    error_path: str
    time: datetime

class JobCreate(JobBase):
    pass


class Job(JobBase):
    id: int
    # owner_id: int

    class Config:
        orm_mode = True


# class UserBase(BaseModel):
#     email: str


# class UserCreate(UserBase):
#     password: str


# class User(UserBase):
#     id: int
#     is_active: bool
#     items: list[Item] = []

#     class Config:
#         orm_mode = True