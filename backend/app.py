from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Aim2Build Part Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
def health():
    return {"ok": True, "service": "aim2build-part-scanner"}


@app.post("/upload")
async def upload_scan(file: UploadFile = File(...)):
    suffix = Path(file.filename or "scan.jpg").suffix.lower() or ".jpg"
    filename = f"scan_{uuid4().hex}{suffix}"
    out_path = UPLOAD_DIR / filename

    content = await file.read()
    out_path.write_bytes(content)

    return {
        "ok": True,
        "filename": filename,
        "url": f"/uploads/{filename}",
        "size": len(content),
    }
