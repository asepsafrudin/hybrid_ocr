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
import fitz  # PyMuPDF for PDF handling
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

# Templates setup
templates = Jinja2Templates(directory="templates")

# Buat direktori uploads jika belum ada
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize processor
processor = create_processor("config.yaml")

# Initialize verification system
verification_system = create_verification_system(
    processor.pattern_manager, "."
)

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
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/tiff",
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} tidak didukung",
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
        asyncio.create_task(
            process_document_background(task_id, str(file_path))
        )

        return JSONResponse(
            {
                "message": "Document processing started",
                "task_id": task_id,
                "filename": file.filename,
                "status": "queued",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing file: {str(e)}"
        )


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
                task_id: {
                    "status": task["status"],
                    "filename": task["filename"],
                }
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
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

        task = processing_tasks[task_id]
        response_data = {
            "task_id": task_id,
            "status": task["status"],
            "filename": task["filename"],
            "created_at": task["created_at"],
            "result": (
                task["result"] if task["status"] == "completed" else None
            ),
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
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

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
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        result = task["result"]
        regions = result.get("regions", [])

        # Filter regions yang perlu verifikasi (confidence < 0.5 atau handwritten)
        verification_regions = []
        for i, region in enumerate(regions):
            confidence = float(region.get("confidence", 1.0))
            region_type = region.get("region_type", "printed")

            if confidence < 0.5 or region_type == "handwritten":
                # Convert bbox to regular Python list
                bbox = region.get("bbox", [0, 0, 100, 100])
                if hasattr(bbox, "tolist"):
                    bbox = bbox.tolist()
                bbox = [int(x) for x in bbox]

                # Skip logo regions (top area, small regions with low confidence)
                if is_logo_region(bbox, region.get("text", "")):
                    continue

                # Create cropped image from region
                cropped_image = create_cropped_image_from_region(
                    task["file_path"], region
                )

                verification_regions.append(
                    {
                        "region_id": int(i),
                        "text": str(region.get("text", "")),
                        "confidence": confidence,
                        "region_type": region_type,
                        "priority_score": float(1.0 - confidence),
                        "cropped_image": cropped_image,
                        "bbox": bbox,
                    }
                )

        response_data = {
            "task_id": task_id,
            "total_regions": int(len(regions)),
            "verification_regions": int(len(verification_regions)),
            "regions": verification_regions,
        }

        # Convert to JSON string with custom encoder, then parse back
        json_str = json.dumps(response_data, cls=NumpyEncoder)
        return JSONResponse(json.loads(json_str))

    except Exception as e:
        print(f"Error getting verification regions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_cropped_image_from_region(file_path: str, region: dict):
    """Create cropped image from region data"""
    import base64
    import cv2
    import numpy as np
    from pathlib import Path

    try:
        # Check if file exists
        if not Path(file_path).exists():
            return create_placeholder_image(region.get("text", "No text"))

        # For PDF files, we need to convert to image first with same DPI as processing
        if file_path.lower().endswith(".pdf"):
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            page = doc[0]  # Get first page
            # Use same DPI as in processing (300 DPI)
            mat = fitz.Matrix(300 / 72, 300 / 72)  # 300 DPI scaling
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            doc.close()
        else:
            # For image files
            img = cv2.imread(file_path)

        if img is None:
            return create_placeholder_image(region.get("text", "No text"))

        # Get bbox coordinates
        bbox = region.get("bbox", [0, 0, 100, 100])
        x1, y1, x2, y2 = [int(coord) for coord in bbox]

        # Debug info
        print(
            f"Debug - Text: '{region.get('text', '')}', BBox: {bbox}, Image shape: {img.shape}"
        )

        # Ensure coordinates are within image bounds
        h, w = img.shape[:2]
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(x1 + 1, min(x2, w))
        y2 = max(y1 + 1, min(y2, h))

        # Add padding for better visibility
        padding = 5
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)

        # Crop the region
        cropped = img[y1:y2, x1:x2]

        if cropped.size == 0:
            return create_placeholder_image(region.get("text", "No text"))

        # Resize if too small for better visibility
        if cropped.shape[0] < 50 or cropped.shape[1] < 100:
            scale_factor = max(50 / cropped.shape[0], 100 / cropped.shape[1])
            new_width = int(cropped.shape[1] * scale_factor)
            new_height = int(cropped.shape[0] * scale_factor)
            cropped = cv2.resize(
                cropped, (new_width, new_height), interpolation=cv2.INTER_CUBIC
            )

        # Encode to base64
        _, buffer = cv2.imencode(".png", cropped)
        return (
            f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
        )

    except Exception as e:
        print(f"Error creating cropped image: {e}")
        return create_placeholder_image(region.get("text", "Error"))


def is_logo_region(bbox, text):
    """Detect if region is part of logo based on position and characteristics"""
    x1, y1, x2, y2 = bbox

    # Logo area coordinates (top-left area of document)
    logo_area = {"x_min": 150, "x_max": 400, "y_min": 100, "y_max": 450}

    # Check if region is in logo area
    in_logo_area = (
        x1 >= logo_area["x_min"]
        and x2 <= logo_area["x_max"]
        and y1 >= logo_area["y_min"]
        and y2 <= logo_area["y_max"]
    )

    # Logo characteristics
    is_small_region = (x2 - x1) < 100 and (y2 - y1) < 60
    is_symbol_text = len(text.strip()) <= 3 and any(
        char in text for char in ["+", ";", "\x1c", "\x14"]
    )

    return in_logo_area and (is_small_region or is_symbol_text)


def create_placeholder_image(text: str, width=200, height=80):
    """Create placeholder image with text"""
    import base64
    import cv2
    import numpy as np

    # Create white background
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Add text
    cv2.putText(
        img,
        text[:20],
        (10, height // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (50, 50, 50),
        1,
    )

    # Encode to base64
    _, buffer = cv2.imencode(".png", img)
    return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"


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
        print(f"Error processing user correction: {e}")
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
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

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

        success = verification_system.process_document_type_validation(
            validation
        )

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
                        row["Keywords"].split(",")
                        if pd.notna(row["Keywords"])
                        else []
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
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

        task = processing_tasks[task_id]
        if task["status"] != "completed":
            raise HTTPException(
                status_code=400, detail=f"Task not completed: {task['status']}"
            )

        metadata = task["result"].get("metadata", {})
        sections = metadata.get("document_sections", [])

        return JSONResponse(
            {
                "task_id": task_id,
                "total_sections": len(sections),
                "sections": sections,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sections/{task_id}/{section_type}")
async def get_specific_section(task_id: str, section_type: str):
    """Get specific section content dari document"""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(
                status_code=404, detail=f"Task {task_id} not found"
            )

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

        section_content = section_api.get_section_content(
            pages_content, section_type
        )

        if section_content:
            return JSONResponse(
                {
                    "task_id": task_id,
                    "section_found": True,
                    "section": section_content,
                }
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


@app.get("/health")
async def health_check():
    """Health check endpoint untuk monitoring"""
    try:
        # Check pattern manager
        stats = processor.pattern_manager.get_pattern_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "patterns_loaded": stats["ocr_patterns"],
            "system": "Enterprise OCR System",
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Health check failed: {str(e)}"
        )


@app.get("/verification", response_class=HTMLResponse)
async def verification_interface(request: Request):
    """Serve verification HTML interface"""
    return templates.TemplateResponse(
        "verification_enhanced.html", {"request": request}
    )


@app.get("/docs")
async def get_docs():
    return {"message": "API Documentation tersedia di /docs"}


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
