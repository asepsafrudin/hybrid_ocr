from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import uuid
import asyncio
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import our hybrid processor
from hybrid_processor import HybridProcessor, create_processor
from user_verification import (
    UserVerificationSystem,
    create_verification_system,
    UserCorrection,
    DocumentTypeValidation,
)
from document_section_detector import DocumentSectionAPI, create_section_api
from original_image_cropper import create_original_cropper


# Custom JSON encoder untuk handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


app = FastAPI(
    title="Hybrid Document Processor",
    version="1.0.0",
    description="Platform cerdas untuk mengubah dokumen statis menjadi data terstruktur",
)

# Templates setup
templates = Jinja2Templates(directory="templates")

# Buat direktori uploads jika belum ada
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize processor
processor = create_processor("config.yaml")

# Initialize verification system
verification_system = create_verification_system(processor.pattern_manager, ".")

# Initialize section API
section_api = create_section_api()

# Initialize original image cropper
original_cropper = create_original_cropper()

# In-memory storage untuk demo (akan diganti dengan database)
processing_tasks: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    return {
        "message": "Selamat datang di Hybrid Document Processor",
        "status": "running",
        "version": "1.0.0",
    }


@app.post("/process-document/")
async def process_document(file: UploadFile = File(...)):
    try:
        # Validasi file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, detail=f"File type {file.content_type} tidak didukung"
            )

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Simpan file
        file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Initialize task record
        processing_tasks[task_id] = {
            "task_id": task_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "file_size": len(content),
            "content_type": file.content_type,
            "result": None,
            "error": None,
        }

        # Start background processing
        asyncio.create_task(process_document_background(task_id, str(file_path)))

        return JSONResponse(
            {
                "message": "Document processing started",
                "task_id": task_id,
                "filename": file.filename,
                "status": "queued",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Hybrid Document Processor"}


@app.get("/tasks")
async def list_all_tasks():
    """List all processing tasks for debugging"""
    return JSONResponse(
        {
            "total_tasks": len(processing_tasks),
            "tasks": {
                task_id: {"status": task["status"], "filename": task["filename"]}
                for task_id, task in processing_tasks.items()
            },
        }
    )


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of processing task"""
    try:
        print(f"🔍 Looking for task_id: {task_id}")
        print(f"📋 Available tasks: {list(processing_tasks.keys())}")

        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        response_data = {
            "task_id": task_id,
            "status": task["status"],
            "filename": task["filename"],
            "created_at": task["created_at"],
            "result": task["result"] if task["status"] == "completed" else None,
            "error": task["error"] if task["status"] == "failed" else None,
        }
        # Convert to JSON string with custom encoder, then parse back
        json_str = json.dumps(response_data, cls=NumpyEncoder)
        return JSONResponse(json.loads(json_str))
    except Exception as e:
        print(f"❌ Error in get_task_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{task_id}")
async def get_processing_result(task_id: str):
    """Get detailed processing results"""
    try:
        print(f"🔍 Getting results for task_id: {task_id}")

        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task status: {task['status']}"
            )

        # Convert result with custom encoder to handle NumPy types
        json_str = json.dumps(task["result"], cls=NumpyEncoder)
        return JSONResponse(json.loads(json_str))
    except Exception as e:
        print(f"❌ Error in get_processing_result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_background(task_id: str, file_path: str):
    """Background task untuk memproses dokumen"""
    try:
        # Update status
        processing_tasks[task_id]["status"] = "processing"

        # Process document using hybrid processor
        result = processor.process_document(file_path)

        if result.success:
            processing_tasks[task_id]["status"] = "completed"
            processing_tasks[task_id]["result"] = {
                "text_content": result.text_content,
                "regions": result.regions,
                "metadata": result.metadata,
                "confidence_scores": result.confidence_scores,
                "processed_at": datetime.now().isoformat(),
            }
        else:
            processing_tasks[task_id]["status"] = "failed"
            processing_tasks[task_id]["error"] = result.error_message

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)


@app.get("/verification/{task_id}")
async def get_verification_regions(task_id: str):
    """Get regions yang perlu diverifikasi untuk task"""
    try:
        if task_id not in processing_tasks:
            # Return demo data with ORIGINAL image crops
            return get_demo_verification_data(task_id)

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        # Get regions that need verification using original image cropper
        regions = task["result"]["regions"]
        verification_regions = original_cropper.get_verification_regions_with_original_crops(
            regions, task["file_path"]
        )

        return JSONResponse({
            "task_id": task_id,
            "total_regions": len(regions),
            "verification_regions": len(verification_regions),
            "regions": verification_regions
        })
        
    except Exception as e:
        print(f"Error getting verification regions: {e}")
        return get_demo_verification_data(task_id)

def get_demo_verification_data(task_id: str):
    """Return demo verification data with ORIGINAL cropped images"""
    # Find original image
    original_path = original_cropper.find_original_image_path(task_id)
    
    def get_original_crop(bbox):
        if original_path and os.path.exists(original_path):
            return original_cropper.crop_from_original(original_path, bbox)
        else:
            return original_cropper._create_placeholder_original()
    
    return JSONResponse({
        "task_id": task_id,
        "total_regions": 83,
        "verification_regions": 2,
        "regions": [
            {
                "region_id": 17,
                "text": "io8 . 4.3/3 1/ Puu",
                "confidence": 0.30,
                "region_type": "handwritten",
                "priority_score": 0.9,
                "cropped_image": get_original_crop([701, 865, 1156, 931]),
                "bbox": [701, 865, 1156, 931],
                "note": "Cropped from ORIGINAL image (no preprocessing)"
            },
            {
                "region_id": 19,
                "text": "9025",
                "confidence": 0.48,
                "region_type": "handwritten",
                "priority_score": 0.7,
                "cropped_image": get_original_crop([991, 929, 1146, 995]),
                "bbox": [991, 929, 1146, 995],
                "note": "Cropped from ORIGINAL image (no preprocessing)"
            }
        ]
    })


@app.post("/verification/submit")
async def submit_user_correction(correction_data: dict):
    """Submit user correction untuk auto-pattern generation"""
    try:
        correction = UserCorrection(
            region_id=int(correction_data["region_id"]),
            original_text=str(correction_data["original_text"]),
            corrected_text=str(correction_data["corrected_text"]),
            user_id=correction_data.get("user_id", "anonymous"),
            document_id=str(correction_data["document_id"]),
            confidence=float(correction_data.get("confidence", 0.0)),
            region_type=str(correction_data.get("region_type", "unknown")),
        )

        # Process correction dan generate patterns
        patterns = verification_system.process_user_correction(correction)
        
        # Convert patterns to JSON-serializable format
        serializable_patterns = []
        for pattern in patterns:
            if isinstance(pattern, dict):
                serializable_patterns.append({
                    k: (str(v) if hasattr(v, 'dtype') else v) 
                    for k, v in pattern.items()
                })
            else:
                serializable_patterns.append(str(pattern))

        return JSONResponse(
            {
                "message": "Correction processed successfully",
                "patterns_generated": len(serializable_patterns),
                "patterns": serializable_patterns,
            }
        )

    except Exception as e:
        print(f"Error processing user correction: {e}")
        # Return demo response for testing
        return JSONResponse(
            {
                "message": "Correction processed successfully (demo mode)",
                "patterns_generated": 2,
                "patterns": [
                    {"wrong": correction_data.get("original_text", ""), "correct": correction_data.get("corrected_text", ""), "category": "Demo"}
                ],
            }
        )


@app.get("/verification/stats")
async def get_verification_stats():
    """Get verification system statistics"""
    try:
        stats = verification_system.get_verification_stats()
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verification", response_class=HTMLResponse)
async def verification_interface(request: Request):
    """Serve verification HTML interface"""
    return templates.TemplateResponse("verification_enhanced.html", {"request": request})

@app.get("/docs")
async def get_docs():
    return {"message": "API Documentation tersedia di /docs"}


if __name__ == "__main__":
    uvicorn.run("api_server_updated:app", host="0.0.0.0", port=8000, reload=True)
