from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, prompts, analyze

app = FastAPI(title="Interview Coach API")

# CORS (simple hardcoded version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(prompts.router, prefix="/prompt", tags=["prompts"])
app.include_router(analyze.router, tags=["analyze"])