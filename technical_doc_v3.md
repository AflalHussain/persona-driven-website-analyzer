# Technical Documentation: API Integration

[Previous sections remain unchanged...]

## 8. REST API Implementation

### Architecture
- FastAPI-based REST API
- Asynchronous request handling
- Background task processing
- Persistent result storage

```python
app = FastAPI(
    title="Website Analysis API",
    description="API for analyzing websites using personas",
    version="1.0.0"
)
```

### Key Components

1. **Request Models**
```python
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
```

2. **Response Models**
```python
class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    message: str

class AnalysisStatus(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

3. **Task Management**
- UUID-based task tracking
- In-memory task status storage
- Persistent result storage
```python
analysis_tasks: Dict[str, str] = {}  # task_id -> status
```

### API Endpoints

1. **Single Persona Analysis**
```python
@app.post("/analyze/single")
async def analyze_single(request: AnalysisRequest, background_tasks: BackgroundTasks)
```

2. **Focus Group Analysis**
```python
@app.post("/analyze/focus-group")
async def analyze_focus_group(request: AnalysisRequest, background_tasks: BackgroundTasks)
```

3. **Analysis Status**
```python
@app.get("/analysis/{task_id}")
async def get_analysis_status(task_id: str)
```

### Result Storage Structure
```
reports/
├── api/
│   ├── {task_id}.json           # Successful analysis results
│   └── {task_id}_error.json     # Error information
```

### Background Processing
- Asynchronous task execution
- Non-blocking request handling
- Progress tracking
- Error handling and recovery

```python
async def run_focus_group_analysis(task_id: str, request: AnalysisRequest):
    try:
        result = await api.analyze_with_focus_group(
            request.url,
            request.persona_template.model_dump(),
            request.num_variations,
            request.max_pages
        )
        # Store result
        with open(f"reports/api/{task_id}.json", 'w') as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        # Store error
        with open(f"reports/api/{task_id}_error.json", 'w') as f:
            json.dump({"error": str(e)}, f)
```

### Status Tracking
- In-memory status tracking
- Persistent result storage
- Status recovery after restart
- Error state preservation

### Error Handling
- Request validation
- Background task error capture
- Persistent error storage
- Detailed error reporting

### Future API Enhancements

1. **Authentication & Authorization**
   - API key management
   - Role-based access control
   - Usage quotas

2. **Rate Limiting**
   - Request throttling
   - Concurrent task limits
   - Resource management

3. **Webhooks**
   - Analysis completion notifications
   - Error reporting
   - Progress updates

4. **Result Management**
   - Result expiration
   - Storage cleanup
   - Result compression

[Previous sections from v2 remain unchanged...]