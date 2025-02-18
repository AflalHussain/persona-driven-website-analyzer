from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import uuid
import json
import os
from datetime import datetime
import logging
import sys
from .analysis_api import WebsiteAnalysisAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Website Analysis API",
    description="API for analyzing websites using personas",
    version="1.0.0"
)

# Input models
class PersonaTemplate(BaseModel):
    role: str
    experience_level: str
    primary_goal: str
    context: str
    additional_details: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    url: str
    persona_template: PersonaTemplate
    num_variations: Optional[int] = 5
    max_pages: Optional[int] = 5

# Response models
class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AnalysisStatus(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Store ongoing tasks
analysis_tasks: Dict[str, str] = {}
api = WebsiteAnalysisAPI()

async def run_single_analysis(task_id: str, request: AnalysisRequest):
    """Background task for single persona analysis"""
    try:
        result = await api.analyze_with_persona(
            request.url,
            request.persona_template.model_dump(),
            request.max_pages
        )
        
        # Save result to file
        output_dir = "reports/api"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{task_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        analysis_tasks[task_id] = "completed"
        
    except Exception as e:
        analysis_tasks[task_id] = "failed"
        # Save error information
        with open(f"{output_dir}/{task_id}_error.json", 'w') as f:
            json.dump({"error": str(e)}, f)

async def run_focus_group_analysis(task_id: str, request: AnalysisRequest):
    """Background task for focus group analysis"""
    try:
        result = await api.analyze_with_focus_group(
            request.url,
            request.persona_template.model_dump(),
            request.num_variations,
            request.max_pages
        )
        
        # Save result to file
        output_dir = "reports/api"
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/{task_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        analysis_tasks[task_id] = "completed"
        
    except Exception as e:
        analysis_tasks[task_id] = "failed"
        # Save error information
        with open(f"{output_dir}/{task_id}_error.json", 'w') as f:
            json.dump({"error": str(e)}, f)

@app.post("/analyze/single", response_model=AnalysisResponse)
async def analyze_single(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start single persona analysis"""
    if not api.validate_persona_template(request.persona_template.model_dump(),):
        raise HTTPException(400, "Invalid persona template")
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = "running"
    
    background_tasks.add_task(run_single_analysis, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Analysis started"
    }

@app.post("/analyze/focus-group", response_model=AnalysisResponse)
async def analyze_focus_group(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start focus group analysis"""
    if not api.validate_persona_template(request.persona_template.model_dump()):
        raise HTTPException(400, "Invalid persona template")
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = "running"
    
    background_tasks.add_task(run_focus_group_analysis, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Analysis started"
    }

@app.get("/analysis/{task_id}", response_model=AnalysisStatus)
async def get_analysis_status(task_id: str):
    """Get the status and result of an analysis task"""
    # Check in-memory tasks first
    status = analysis_tasks.get(task_id)
    
    if status is None:
        # If not in memory, check if completed report exists
        try:
            with open(f"reports/api/{task_id}.json", 'r') as f:
                result = json.load(f)
                return {
                    "status": "completed",
                    "result": result
                }
        except FileNotFoundError:
            # Check if error report exists
            try:
                with open(f"reports/api/{task_id}_error.json", 'r') as f:
                    error_info = json.load(f)
                    return {
                        "status": "failed",
                        "error": error_info["error"]
                    }
            except FileNotFoundError:
                raise HTTPException(404, "Analysis task not found")
    
    # Handle in-memory task status
    if status == "completed":
        try:
            with open(f"reports/api/{task_id}.json", 'r') as f:
                result = json.load(f)
            return {
                "status": status,
                "result": result
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": "Result file not found"
            }
    elif status == "failed":
        try:
            with open(f"reports/api/{task_id}_error.json", 'r') as f:
                error_info = json.load(f)
            return {
                "status": status,
                "error": error_info["error"]
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "error": "Error information not found"
            }
    else:
        return {
            "status": status
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)