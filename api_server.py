import asyncio
import uuid
import logging
from pathlib import Path
from typing import Dict, List
import json

from fastapi import (FastAPI, File, UploadFile, WebSocket, Depends,
                     WebSocketDisconnect, BackgroundTasks, HTTPException)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Proyek Lokal
from .database import get_db, engine, SessionLocal
from . import models
from .vector_store import VectorStore
# Placeholder for your actual processor.
# from hybrid_processor import HybridDocumentProcessor

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Hybrid Document Processor API",
    description="API for processing documents with a hybrid OCR approach.",
    version="1.0.0"
)

# Inisialisasi Vector Store sebagai singleton
vector_store = VectorStore()

# Buat tabel di database jika belum ada
models.Base.metadata.create_all(bind=engine)

# --- CORS Middleware ---
# Allows the frontend (e.g., React on localhost:3000) to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdate(BaseModel):
    step: int
    total_steps: int
    message: str
    progress: float
    status: str = "processing"

# --- Pydantic Models for API Data Structure ---
class ProcessResponse(BaseModel):
    task_id: str
    filename: str
    message: str

# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_status_update(self, task_id: str, update: StatusUpdate):
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            await websocket.send_json(update.dict())

manager = ConnectionManager()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Background OCR Processing Task ---
async def run_ocr_processing(task_id: uuid.UUID, file_path: Path, db: Session):
    """
    Performs the full document processing pipeline: OCR, DB storage, and vector embedding.
    This is where you will integrate your HybridDocumentProcessor.
    """
    task_id_str = str(task_id)
    try:
        task = db.query(models.ProcessingTask).filter(models.ProcessingTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id_str} not found in DB for processing.")
            return

        task.status = models.TaskStatus.PROCESSING
        db.commit()

        total_steps = 6
        # processor = HybridDocumentProcessor() # Initialize your processor

        # --- Step 1-4: Simulate Hybrid OCR Processing ---
        # In reality, you would call your processor here.
        # processor.process(file_path)
        await manager.send_status_update(task_id_str, StatusUpdate(step=1, total_steps=total_steps, message="Step 1/6: Converting PDF...", progress=15.0))
        await asyncio.sleep(1)
        await manager.send_status_update(task_id_str, StatusUpdate(step=2, total_steps=total_steps, message="Step 2/6: Detecting Layout...", progress=30.0))
        await asyncio.sleep(2)
        await manager.send_status_update(task_id_str, StatusUpdate(step=3, total_steps=total_steps, message="Step 3/6: Extracting Text...", progress=50.0))
        await asyncio.sleep(3)
        await manager.send_status_update(task_id_str, StatusUpdate(step=4, total_steps=total_steps, message="Step 4/6: Merging Results...", progress=65.0))
        await asyncio.sleep(1)

        # --- Step 5: Save structured data to PostgreSQL ---
        await manager.send_status_update(task_id_str, StatusUpdate(step=5, total_steps=total_steps, message="Step 5/6: Storing structured data...", progress=80.0))
        
        # This is a simulated output from your HybridDocumentProcessor
        ocr_result = {
            "source_file": file_path.name, "page_count": 1,
            "annotations": [
                {"id": "block_001", "label": "Title", "text": "Laporan Keuangan Tahunan", "confidence": 0.95},
                {"id": "block_002", "label": "Printed", "text": "Berdasarkan hasil audit yang telah dilakukan...", "confidence": 0.92},
                {"id": "block_003", "label": "Handwriting", "text": "Disetujui oleh Asep", "confidence": 0.88}
            ]
        }
        task.output_data = ocr_result
        db.commit()
        await asyncio.sleep(1)

        # --- Step 6: Generate and save embeddings to Vector Store ---
        await manager.send_status_update(task_id_str, StatusUpdate(step=6, total_steps=total_steps, message="Step 6/6: Creating semantic index...", progress=95.0))
        
        docs_to_embed = [ann["text"] for ann in ocr_result.get("annotations", [])]
        metadatas = [{"task_id": task_id_str, "block_id": ann["id"], "label": ann["label"]} for ann in ocr_result.get("annotations", [])]
        ids = [f"{task_id_str}_{ann['id']}" for ann in ocr_result.get("annotations", [])]
        
        vector_store.add_documents(documents=docs_to_embed, metadatas=metadatas, ids=ids)
        
        task.status = models.TaskStatus.COMPLETED
        db.commit()
        await manager.send_status_update(task_id_str, StatusUpdate(step=6, total_steps=total_steps, message="Processing complete!", progress=100.0, status="completed"))

    except Exception as e:
        logger.error(f"Error processing task {task_id_str}: {e}", exc_info=True)
        db.rollback()
        task = db.query(models.ProcessingTask).filter(models.ProcessingTask.id == task_id).first()
        if task:
            task.status = models.TaskStatus.FAILED
            db.commit()
        await manager.send_status_update(task_id_str, StatusUpdate(step=0, total_steps=total_steps, message=f"Error: {e}", progress=100.0, status="failed"))
    finally:
        if file_path.exists():
            file_path.unlink()
        db.close()

# --- API Endpoints ---
@app.post("/process-document/", response_model=ProcessResponse)
async def create_process_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a document, saves it, creates a task record in the DB,
    and starts the full background processing pipeline.
    """
    # Di dunia nyata, ini akan diunggah ke S3/MinIO dan key-nya disimpan.
    input_file_key = f"temp/{uuid.uuid4()}_{file.filename}"
    file_path = Path(input_file_key)
    file_path.parent.mkdir(exist_ok=True, parents=True)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    new_task = models.ProcessingTask(input_file_key=input_file_key)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # Jalankan tugas di latar belakang dengan sesi DB baru
    background_tasks.add_task(run_ocr_processing, new_task.id, file_path, SessionLocal())

    return ProcessResponse(task_id=str(new_task.id), filename=file.filename, message="Document processing started.")

@app.websocket("/ws/status/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for clients to receive real-time status updates.
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(task_id)