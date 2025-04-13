from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from routes.demo import router as demoRouter
from routes.ask_chat import router as askChatRouter

app = FastAPI()

# Mount static files first
app.mount("/v1/static", StaticFiles(directory="static", html=True), name="static")

# Sau đó mới thêm middleware và routes
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

# Then configure API routes
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(demoRouter, tags=["Demo"])
v1_router.include_router(askChatRouter, tags=["Ask Chat"])
app.include_router(v1_router)

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

