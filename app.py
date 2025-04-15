from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from routes.demo import router as demoRouter
from routes.ask_chat import router as askChatRouter
from routes.upload import router as uploadRouter
from routes.chatbot import router as chatbotRouter
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
import sys
from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = find_dotenv()
if env_path:
    logger.info(f"Loading environment variables from {env_path}")
    load_dotenv(env_path)
else:
    logger.warning("No .env file found. Using environment variables from system.")

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collection_db.document import DocumentModel
from collection_db.page import Page
from collection_db.chatbot import Chatbot

app = FastAPI()

# Mount static files first
app.mount("/v1/static", StaticFiles(directory="static", html=True), name="static")

# Configure CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure API routes
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(demoRouter, tags=["Demo"])
v1_router.include_router(askChatRouter, tags=["Ask Chat"])
v1_router.include_router(uploadRouter, prefix="/pdf", tags=["PDF Processing"])
v1_router.include_router(chatbotRouter, prefix="/chatbot", tags=["Chatbot"])
app.include_router(v1_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# Initialize Beanie
@app.on_event("startup")
async def init_db():
    try:
        # Get MongoDB connection details from environment variables
        DATABASE_URL = os.getenv("DATABASE_URL")
        DATABASE_NAME = os.getenv("DATABASE_NAME")
        
        logger.info(f"DATABASE_URL: {'Set' if DATABASE_URL else 'Not set'}")
        logger.info(f"DATABASE_NAME: {'Set' if DATABASE_NAME else 'Not set'}")
        
        if not DATABASE_URL or not DATABASE_NAME:
            raise ValueError("DATABASE_URL and DATABASE_NAME must be set in environment variables")
            
        logger.info(f"Connecting to MongoDB at {DATABASE_URL}")
        
        # Create Motor client
        client = AsyncIOMotorClient(DATABASE_URL)
        
        # Initialize beanie with the document models
        await init_beanie(
            database=client[DATABASE_NAME],
            document_models=[
                DocumentModel,
                Page,
                Chatbot
            ]
        )
        logger.info(f"Database {DATABASE_NAME} initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

# OpenAPI schema configuration
def my_schema():
    openapi_schema = get_openapi(
        title="AI Content Safeguard API",
        version="1.0",
        routes=app.routes,
    )
    openapi_schema["info"] = {
        "title": "AI Content Safeguard API",
        "version": "1.0",
        "description": "AI Content Safeguard API",
        "contact": {
            "name": "Get Help with this API",
            "url": "mailto:hungdv1610@gmail.com",
            "email": "hungdv1610@gmail.com",
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = my_schema

@app.get("/", include_in_schema=False, tags=['Documentation'])
async def redirect():
    return RedirectResponse("/v1/demo")

