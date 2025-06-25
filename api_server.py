from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
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

# Buat direktori uploads jika belum ada
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize processor
processor = create_processor("config.yaml")

# Initialize verification system
verification_system = create_verification_system(processor.pattern_manager, ".")

# Initialize section API
section_api = create_section_api()

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
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        # Load original image
        import cv2

        image = cv2.imread(task["file_path"])
        if image is None:
            raise HTTPException(status_code=500, detail="Cannot load original image")

        # Get verification regions
        regions = task["result"]["regions"]
        verification_regions = verification_system.get_regions_for_verification(
            regions, image, task_id
        )

        return JSONResponse(
            {
                "task_id": task_id,
                "total_regions": len(regions),
                "verification_regions": len(verification_regions),
                "regions": [
                    {
                        "region_id": r.region_id,
                        "text": r.text,
                        "confidence": r.confidence,
                        "region_type": r.region_type,
                        "priority_score": r.priority_score,
                        "cropped_image": r.cropped_image_b64,
                    }
                    for r in verification_regions
                ],
            }
        )

    except Exception as e:
        logger.error(f"Error getting verification regions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verification/submit")
async def submit_user_correction(correction_data: dict):
    """Submit user correction untuk auto-pattern generation"""
    try:
        correction = UserCorrection(
            region_id=correction_data["region_id"],
            original_text=correction_data["original_text"],
            corrected_text=correction_data["corrected_text"],
            user_id=correction_data.get("user_id", "anonymous"),
            document_id=correction_data["document_id"],
            confidence=correction_data.get("confidence", 0.0),
            region_type=correction_data.get("region_type", "unknown"),
        )

        # Process correction dan generate patterns
        patterns = verification_system.process_user_correction(correction)

        return JSONResponse(
            {
                "message": "Correction processed successfully",
                "patterns_generated": len(patterns),
                "patterns": patterns,
            }
        )

    except Exception as e:
        logger.error(f"Error processing user correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verification/stats")
async def get_verification_stats():
    """Get verification system statistics"""
    try:
        stats = verification_system.get_verification_stats()
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/document-types/suggestions/{task_id}")
async def get_document_type_suggestions(task_id: str):
    """Get ML-suggested document types untuk task"""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        metadata = task["result"].get("metadata", {})
        suggestion = metadata.get("suggested_document_type")

        if suggestion:
            return JSONResponse(
                {
                    "task_id": task_id,
                    "has_suggestion": True,
                    "suggestion": suggestion,
                    "current_type": metadata.get("document_type", "General"),
                }
            )
        else:
            return JSONResponse(
                {
                    "task_id": task_id,
                    "has_suggestion": False,
                    "current_type": metadata.get("document_type", "General"),
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/document-types/validate")
async def validate_document_type(validation_data: dict):
    """Submit user validation untuk document type suggestion"""
    try:
        validation = DocumentTypeValidation(
            document_id=validation_data["document_id"],
            suggested_type=validation_data["suggested_type"],
            user_action=validation_data["user_action"],  # accept/reject/modify
            final_type=validation_data["final_type"],
            user_id=validation_data.get("user_id", "anonymous"),
            confidence=validation_data.get("confidence", 0.0),
            keywords=validation_data.get("keywords", []),
        )

        success = verification_system.process_document_type_validation(validation)

        return JSONResponse(
            {
                "message": "Document type validation processed",
                "success": success,
                "action": validation.user_action,
                "final_type": validation.final_type,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/document-types/list")
async def list_document_types():
    """List all available document types"""
    try:
        import pandas as pd

        df = pd.read_csv("Document_Types_Template.csv")
        types = []
        for _, row in df.iterrows():
            types.append(
                {
                    "type": row["Document_Type"],
                    "keywords": (
                        row["Keywords"].split(",") if pd.notna(row["Keywords"]) else []
                    ),
                    "description": row.get("Description", ""),
                    "enabled": row.get("Enabled", True),
                }
            )
        return JSONResponse({"document_types": types})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sections/{task_id}")
async def get_document_sections(task_id: str):
    """Get detected sections untuk multi-page document"""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        metadata = task["result"].get("metadata", {})
        sections = metadata.get("document_sections", [])

        return JSONResponse(
            {"task_id": task_id, "total_sections": len(sections), "sections": sections}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sections/{task_id}/{section_type}")
async def get_specific_section(task_id: str, section_type: str):
    """Get specific section content dari document"""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        # Get original processing result
        result = task["result"]

        # Extract pages content from regions (simplified)
        # In real implementation, you'd reconstruct pages from regions
        pages_content = [result["text_content"]]  # Simplified for demo

        section_content = section_api.get_section_content(pages_content, section_type)

        if section_content:
            return JSONResponse(
                {"task_id": task_id, "section_found": True, "section": section_content}
            )
        else:
            return JSONResponse(
                {
                    "task_id": task_id,
                    "section_found": False,
                    "message": f"Section '{section_type}' not found",
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/docs")
async def get_docs():
    return {"message": "API Documentation tersedia di /docs"}


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
