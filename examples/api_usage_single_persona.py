import asyncio
import httpx
import json
import time

async def analyze_website():
    # API endpoints
    BASE_URL = "http://localhost:8000"
    
    # Example persona template
    analysis_request = {
        "url": "https://www.w3schools.com",
        "persona_template": {
            "role": "Developer",
            "experience_level": "Senior",
            "primary_goal": "Find contract work",
            "context": "Looking for remote opportunities",
            "additional_details": {
                "preferred_stack": "Full-stack",
                "availability": "Part-time"
            }
        },
        "max_pages": 3
    }
    
    async with httpx.AsyncClient() as client:
        # Start analysis
        response = await client.post(f"{BASE_URL}/analyze/single", json=analysis_request)
        task_data = response.json()
        task_id = task_data["task_id"]
        print(f"Analysis started with task ID: {task_id}")
        
        # Poll for results
        while True:
            status_response = await client.get(f"{BASE_URL}/analysis/{task_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                print("\nAnalysis completed!")
                print("\nResults:")
                print(json.dumps(status_data["result"], indent=2))
                break
            elif status_data["status"] == "failed":
                print(f"\nAnalysis failed: {status_data.get('error', 'Unknown error')}")
                break
            else:
                print("Analysis in progress...")
                await asyncio.sleep(5)  # Wait 5 seconds before checking again

if __name__ == "__main__":
    asyncio.run(analyze_website())