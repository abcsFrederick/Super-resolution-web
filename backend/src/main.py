import re
import os
import time
import subprocess
from datetime import datetime
import json

from typing import Union
from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

import omero
from omero.gateway import BlitzGateway
from omero.cli import cli_login


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


origins = [
    "http://localhost:8099",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# shared_partition = '/mnt/hpc/webdata/server/' + os.getenv('host') + '/'
shared_partition = '/mnt/hpc/webdata/server/fsivgl-cellt01d'
# shared_partition = '/opt/viv/omero_test/test_partition'

def connect_to_omero(user, password, host, port=4064, suid=None):
    print(type(suid))
    print(host)
    if suid != None:
        conn = BlitzGateway( host=host, port=port)
        conn.connect(sUuid=suid)
    else:
        conn = BlitzGateway(user, password, host=host, port=port)
        conn.connect()
    print("conn obj:")
    print(conn.connect())
    print()
    user = conn.getUser()
    print("Current user:")
    print("   ID:", user.getId())
    print("   Username:", user.getName())
    print("   Full Name:", user.getFullName())
    print("Member of:")
    for g in conn.getGroupsMemberOf():
        print("   ID:", g.getName(), " Name:", g.getId())
    group = conn.getGroupFromContext()
    print("Current group: ", group.getName())
    return conn

def hpc_configure(job_name, env_name, script, modules, *args, **kwargs):
    script = script
    batchscript = """#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --job-name={name}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres={gres}
#SBATCH --output={shared_partition_log}/slurm-%x.%j.out
#SBATCH --error={shared_partition_log}/slurm-%x.%j.err

source /mnt/nasapps/production/miniconda/23.1.0/etc/profile.d/conda.sh
module load {modules}
mkdir -p {shared_partition_tmp_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
"""
    shared_partition_log = os.path.join(shared_partition, 'logs')
    shell_path = os.path.join(shared_partition, 'shells')
    modules_path = os.path.join(shared_partition, 'modules')
    shared_partition_tmp_directory = os.path.join(shared_partition, 'tmp')
    python_script_path = os.path.join(modules_path, script)

    shared_partition_requirements_directory = os.path.join(shared_partition, 'env')

    if env_name:
        env = os.path.join(shared_partition_requirements_directory, env_name)
        pip_command = """conda activate {env}
"""
        pip_script = pip_command.format(env=env)

        batchscript += pip_script

    exec_command = """python {pythonScriptPath} --directory {shared_partition_tmp_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID """  # noqa: E501


    gres = kwargs.pop('gres', 'gpu:v100:1')
    for name in kwargs.keys():
        arg = '--' + str(name) + ' ' + str(kwargs[name]) + ' '
        exec_command += arg

    batchscript += exec_command

    if not os.path.isdir(shared_partition_log):
        os.mkdir(shared_partition_log)
    if not os.path.isdir(shell_path):
        os.mkdir(shell_path)
    if not os.path.isdir(modules_path):
        os.mkdir(modules_path)
    if not os.path.isdir(shared_partition_tmp_directory):
        os.mkdir(shared_partition_tmp_directory)

    script = batchscript.format(name=job_name,
                                gres=gres,
                                shared_partition_log=shared_partition_log,
                                shared_partition_tmp_directory=shared_partition_tmp_directory,
                                modules=' '.join(modules),
                                pythonScriptPath=python_script_path)

    shell_script_path = os.path.join(shell_path, job_name + '.sh')
    with open(shell_script_path, 'w') as sh:
        sh.write(script)
    try:
        args = ['sbatch']
        args.append(sh.name)
        res = subprocess.check_output(args).strip()
        if not res.startswith(b'Submitted batch'):
            return None
        slurm_job_id = int(res.split()[-1])
        print('slurm job id: ' + str(slurm_job_id))
        return slurm_job_id
    except Exception:
        traceback.print_exc()


@app.get("/api/v1/info")
def getInfo(token: str, user: str, data_id: str, data_type: str):
    # conn = connect_to_omero("", "", "nife-images-dev.cancer.gov",suid=suid)
    conn = connect_to_omero(user, token, "nife-images-dev.cancer.gov")
    data = conn.getObject(data_type, data_id)
    print(data_type, data_id)
    # conn._closeSession()
    print(data)
    info = { "name": data.name }
    return info

def download_omero_image(imageId, suid, dataset_dir):
    # if image.getFileset() is None:
    #     print("No files to download for Image", image.id)
    # # image_dir = os.path.join(dataset_dir, image.name)
    # # If each image is a single file, or are guaranteed not to clash
    # # then we don't need image_dir. Can use dataset_dir instead
    
    # fileset = image.getFileset()
    # if fileset is None:
    #     print('Image has no Fileset')
    # dc.download_fileset(conn, fileset, dataset_dir)
    # with cli_login("tianyi_test@nife-images-dev.cancer.gov", "-w", "mivsyv-dYfrit-wezmy6") as cli:
    with cli_login("-k", suid, "nife-images-dev.cancer.gov") as cli:
        cli.invoke(["download", f'Image:{imageId}', dataset_dir])


def get_log_path(slurm_id, job_name):
    err_file = f"{shared_partition}/logs/slurm-{job_name}.{slurm_id}.err"
    log_file = f"{shared_partition}/logs/slurm-{job_name}.{slurm_id}.out"
    return log_file, err_file

@app.post("/api/v1/submit")
def submit(token: str, user: str, data_id: str, data_type: str, data_name: str, db: Session = Depends(get_db)):
    job_name = data_name
    job_type = 'Super-resolution'
    description = ''


    omero_host = 'nife-images-dev.cancer.gov'

    slurm_id = str(hpc_configure(job_name, "cycle_gan_infer", "super-resolution-entry.py", "",
                           user=user, token=token, data_id=data_id, data_type=data_type, omero_host=omero_host))

    log_file, err_file = get_log_path(slurm_id, job_name)
    # return slurm_id
    job = schemas.JobCreate(
        title=job_name,
        description=description,
        job_type=job_type,
        slurm_id=slurm_id,
        status=2,
        log_path=log_file,
        error_path=err_file,
        time=datetime.now()
    )

    crud.create_job(db=db, job=job)
    return { 'msg':'Job has been submitted with Slurm Id: ' + slurm_id, 'slurm_id': slurm_id, 'job_name': job_name, 'job_type': job_type}


@app.post("/api/v1/merge_channels/submit")
def merge_submit(data_path: str, db: Session = Depends(get_db)):
    job_name = os.path.basename(data_path)
    job_type = 'Merge_channels'
    description = ''


    omero_host = 'nife-images-dev.cancer.gov'

    slurm_id = str(hpc_configure(job_name, "merge_channels", "Merge_channels.py", "", data_path=data_path))

    log_file, err_file = get_log_path(slurm_id, job_name)

    # return slurm_id
    job = schemas.JobCreate(
        title=job_name,
        description=description,
        job_type=job_type,
        slurm_id=slurm_id,
        status=2,
        log_path=log_file,
        error_path=err_file,
        time=datetime.now()
    )
    crud.create_job(db=db, job=job)
    return { 'msg':'Job has been submitted with Slurm Id: ' + slurm_id, 'slurm_id': slurm_id, 'job_name': job_name, 'job_type': job_type}


@app.get("/api/v1/checklogs")
def logs(slurm_id: Union[str, None] = None, job_name: Union[str, None] = None, db: Session = Depends(get_db)):
    jobs = crud.get_jobs(db, skip=0, limit=100)

    log_lines = None
    err_lines = None
    if not slurm_id or not job_name:
        return { 'status': '', 'logs': log_lines, 'error': err_lines, 'records': jobs}

    args = 'squeue -j {}'.format(slurm_id)
    output = subprocess.Popen(args,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out_put = output.communicate()[0]
    found = re.findall(slurm_id, out_put.decode())
    status = 2
    if len(found) == 0:
        job = crud.get_job_by_id(db, slurm_id=slurm_id)
        status = 3
        if job.status != 3:
            value = {'status': status}
            crud.update_job(db, slurm_id, value)
            jobs = crud.get_jobs(db, skip=0, limit=100)

    log_file, err_file = get_log_path(slurm_id, job_name)

    if os.path.exists(log_file):
        logfile = open(log_file,"r")
        log_lines = logfile.readlines()
    if os.path.exists(err_file):
        errfile = open(err_file,"r")
        err_lines = errfile.readlines()

    return { 'status': status, 'logs': log_lines, 'error': err_lines, 'records': jobs}


@app.post("/api/v1/job/", response_model=schemas.Job)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    return crud.create_job(db=db, job=job)

@app.get("/api/v1/jobs/", response_model=list[schemas.Job])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = crud.get_jobs(db, skip=skip, limit=limit)
    return jobs

@app.put("/api/v1/job/", response_model=list[schemas.Job])
def update_job(slurm_id: str, status: int, db: Session = Depends(get_db)):
    value = {'status': status}
    job = crud.update_job(db, slurm_id, value)
    return job

@app.delete("/api/v1/job/", response_model=list[schemas.Job])
def delete_jobs(id: int, db: Session = Depends(get_db)):
    job = crud.delete_job(db, id)
    return job


def create_folder_structure_json(path): 
    # Initialize the result dictionary with folder 
    # name, type, and an empty list for children 
    result = {'title': os.path.basename(path), 
              'file_type': 'folder', 
              'folder_path': path,
              'children': []} 
  
    # Check if the path is a directory 
    if not os.path.isdir(path): 
        return result 
  
    # Iterate over the entries in the directory 
    for entry in os.listdir(path): 
       # Create the full path for the current entry 
        entry_path = os.path.join(path, entry) 
  
        # If the entry is a directory, recursively call the function 
        if os.path.isdir(entry_path): 
            result['children'].append(create_folder_structure_json(entry_path)) 
        # If the entry is a file, create a dictionary with name and type 
        else: 
            result['children'].append({'title': entry, 'file_type': 'img'}) 
  
    return result


@app.get("/api/v1/subfolders/")
def getSubfolders(path: str):
    folder_json = create_folder_structure_json(path) 

    folder_json_str = json.dumps(folder_json, indent=4) 

    return [folder_json]