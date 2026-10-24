from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routes import health, chat, conversations, tools, memory, agents, workflows, vision, voice
from app.utils.logger import logger

settings = get_settings()

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Intelligent Agentic Operations Platform powered by Hugging Face open-weight models.",
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include All Routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(tools.router)
app.include_router(memory.router)
app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(vision.router)
app.include_router(voice.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing AgentOps SQLite Database & Vector Store...")
    init_db()
    logger.info("AgentOps AI Backend (Hugging Face Powered) is Ready!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AgentOps AI Backend stopped.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)