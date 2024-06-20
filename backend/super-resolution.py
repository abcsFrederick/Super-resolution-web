import uvicorn
from uvicorn.config import LOGGING_CONFIG
from src.main import app

if __name__ == "__main__":
    uvicorn.run("super-resolution:app", host="0.0.0.0", port=8098, reload=True, log_config='./config.yml')
