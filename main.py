from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config.logger import get_logger, setup_logging
from config.logger import log_time_taken

setup_logging()
logger = get_logger(__name__)

app = FastAPI()

origins = [
    "http://localhost:*",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import (
    health_check,
    generate_video,
    gen_script,
    upload_vid_gen,
    audio_to_vid
)

app.include_router(health_check.router, prefix="")
app.include_router(generate_video.router,prefix="")
app.include_router(gen_script.router,prefix="")
app.include_router(upload_vid_gen.router,prefix="")
app.include_router(audio_to_vid.router,prefix="")
