from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Backend is running. Visit /docs"}

@router.get("/health")
def health():
    return {"status": "healthy"}