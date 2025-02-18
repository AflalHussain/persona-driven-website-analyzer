# run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api.fast_api:app", host="0.0.0.0", port=8000, reload=True)