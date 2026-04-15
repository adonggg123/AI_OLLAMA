from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import uvicorn

app = FastAPI()

# Enable CORS so the Flutter app can talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str


# Local Ollama URL (Default port 11434)
OLLAMA_URL = "http://localhost:11434/api/generate"


# Root route
@app.get("/")
async def root():
    return {"message": "Offline Ollama AI Server is linked and running...."}


# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    payload = {
        "model": "kimi-k2.5:cloud",  # Make sure this model is already pulled in Ollama
        "prompt": request.prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(OLLAMA_URL, json=payload, timeout=120.0)
            response.raise_for_status()
            result = response.json()

            if isinstance(result, dict):
                ai_text = (
                    result.get("response")
                    or result.get("text")
                    or result.get("output")
                    or result.get("choices")
                )
            else:
                ai_text = str(result)

            return {"response": ai_text or "No response from AI"}

    except httpx.HTTPStatusError as e:
        detail = None
        try:
            error_json = e.response.json()
            detail = (
                error_json.get("detail")
                or error_json.get("message")
                or error_json.get("error")
                or json.dumps(error_json)
            )
        except Exception:
            detail = e.response.text or str(e)

        print(f"Ollama HTTP error: {detail}")
        raise HTTPException(status_code=e.response.status_code, detail=detail)

    except httpx.RequestError as e:
        print(f"Error connecting to Ollama: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to Ollama: {e}")

    except Exception as e:
        print(f"Unexpected error while calling Ollama: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on your Wi-Fi to connect
    uvicorn.run(app, host="0.0.0.0", port=8000)