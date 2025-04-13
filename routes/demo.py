from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import HTMLResponse
import os
import json

router = APIRouter()

@router.get("/demo")
async def demo():
    # Đọc file HTML từ thư mục static
    html_path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)