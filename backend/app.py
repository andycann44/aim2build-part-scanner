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



@app.post("/api/sessions")
async def create_scan_session(files: list[UploadFile] = File(...)):
    session_id = f"session_{uuid4().hex}"
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for index, file in enumerate(files, start=1):
        suffix = Path(file.filename or f"photo_{index}.jpg").suffix.lower() or ".jpg"
        filename = f"original_{index}{suffix}"
        out_path = session_dir / filename

        content = await file.read()
        out_path.write_bytes(content)

        saved.append({
            "index": index,
            "filename": filename,
            "local_path": str(out_path),
            "url": f"/uploads/{session_id}/{filename}",
            "size": len(content),
        })

    return {
        "ok": True,
        "session_id": session_id,
        "color_id": 0,
        "photo_count": len(saved),
        "status": "uploaded_local",
        "photos": saved,
    }


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
