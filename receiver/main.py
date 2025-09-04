import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

SAVE_ROOT = Path(os.getenv("SAVE_DIR", "/data")).resolve()

app = FastAPI(title="ComfyUI Receiver", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_files(
    file: List[UploadFile] = File(..., description="One or more files"),
    subdir: str | None = Form(default=None, description="Optional subdirectory under SAVE_DIR"),
):
    if not SAVE_ROOT.exists():
        try:
            SAVE_ROOT.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create save dir: {e}")

    # sanitize subdir: prevent path traversal
    target_dir = SAVE_ROOT
    if subdir:
        normalized = Path(subdir).as_posix().strip().lstrip("/.")
        if normalized:
            target_dir = (SAVE_ROOT / normalized).resolve()
            if not str(target_dir).startswith(str(SAVE_ROOT)):
                raise HTTPException(status_code=400, detail="Invalid subdir path")

    target_dir.mkdir(parents=True, exist_ok=True)

    results = []
    today = datetime.now().strftime("%Y-%m-%d")
    dated_dir = (target_dir / today)
    dated_dir.mkdir(parents=True, exist_ok=True)

    for f in file:
        # save with timestamp + original name to avoid collisions
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = Path(f.filename).name if f.filename else "upload.bin"
        dst_path = dated_dir / f"{ts}_{safe_name}"
        try:
            with dst_path.open("wb") as out:
                shutil.copyfileobj(f.file, out)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed saving {safe_name}: {e}")
        finally:
            await f.close()
        results.append({
            "filename": dst_path.name,
            "path": str(dst_path),
            "size": dst_path.stat().st_size,
        })

    return JSONResponse(content={"saved": results})
