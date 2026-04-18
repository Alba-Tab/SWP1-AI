from fastapi import FastAPI, HTTPException, Request
from models import GenerateRequest, GenerateResponse
from llm_client import generate_diagram

app = FastAPI(title="sp1-ai-service")


@app.middleware("http")
async def log_raw_body(request: Request, call_next):
    body = await request.body()
    print(f"RAW BODY [{request.method} {request.url.path}]: {body[:500]}")
    print(f"HEADERS: {dict(request.headers)}")
    # Re-inject the body so downstream handlers (FastAPI JSON parsing) can read it
    request._body = body
    response = await call_next(request)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    
    print(f"DEBUG - Cuerpo recibido: {request}")
    try:
        return await generate_diagram(request)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"No se pudo generar el diagrama: {str(e)}")
