from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import documents, chat, reports, timeline, medications, emergency, access, insurance

app = FastAPI(
    title="Healthcare Medical Vault AI & Document Intelligence Backend",
    description="Standalone AI & Document Intelligence backend for secure personal medical records, RAG chat, report comparison, health timeline, emergency QR snapshots, doctor access grants, and insurance discovery.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(timeline.router)
app.include_router(medications.router)
app.include_router(emergency.router)
app.include_router(access.router)
app.include_router(insurance.router)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "service": "Healthcare Medical Vault AI Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
