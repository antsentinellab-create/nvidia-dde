"""
DSS Web UI - FastAPI Application
提供 Web 介面給工程部門共用平台
"""
import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Import repository layer
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from db.repository import get_recent_reviews, get_review_by_id, save_review
from db.models import engine, init_db
from engine.task_queue import get_task_queue, init_task_queue

# Initialize FastAPI app
app = FastAPI(
    title="DSS Web UI",
    description="設計審查系統 Web 介面",
    version="3.0.0"
)

# CORS middleware (for future API usage)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/history.db")
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")


def get_database_backend():
    """獲取資料庫後端資訊"""
    return "PostgreSQL" if IS_POSTGRESQL else "SQLite"


@app.on_event("startup")
async def startup_event():
    """啟動時初始化資料庫和任務佇列"""
    init_db()
    await init_task_queue()
    
    # 添加全局變數到 Jinja2 環境
    templates.env.globals["get_database_backend"] = get_database_backend


# Dependency to inject database info into templates
async def inject_db_info(request: Request, call_next):
    """Middleware to inject database backend info"""
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首頁 - 顯示最近審查記錄"""
    try:
        # Initialize database if needed
        init_db()
        
        reviews = get_recent_reviews(limit=10)
        
        return templates.TemplateResponse(
            request,
            "index.html",
            {"reviews": reviews}
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": str(e)}
        )


@app.get("/review/new", response_class=HTMLResponse)
async def review_new(request: Request):
    """提交新審查表單頁面"""
    return templates.TemplateResponse(
        request,
        "review_form.html",
        {}
    )


@app.post("/review/submit")
async def review_submit(
    request: Request,
    project_name: str = Form(...),
    specification: str = Form(...)
):
    """提交審查處理 - 使用非同步任務"""
    try:
        # 提交至非同步任務佇列
        task_queue = get_task_queue()
        task_id = await task_queue.submit_task(project_name, specification)
        
        return templates.TemplateResponse(
            request,
            "review_success.html",
            {
                "project_name": project_name,
                "task_id": task_id,
                "message": "審查已提交，正在背景處理中..."
            }
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "review_form.html",
            {"error": str(e)}
        , status_code=400)


@app.get("/review/{review_id}", response_class=HTMLResponse)
async def review_detail(request: Request, review_id: int):
    """審查詳情頁面"""
    try:
        review = get_review_by_id(review_id)
        
        if not review:
            return templates.TemplateResponse(
                request,
                "404.html",
                {"message": "找不到該審查記錄"}
            , status_code=404)
        
        return templates.TemplateResponse(
            request,
            "review_detail.html",
            {"review": review}
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": str(e)}
        )


@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_base(request: Request):
    """知識庫瀏覽頁面（唯讀）"""
    try:
        knowledge_dir = Path(__file__).parent.parent / "knowledge"
        
        knowledge_files = {
            "roles": [],
            "standards": [],
            "risk_templates": []
        }
        
        # Scan knowledge directories
        for category in knowledge_files.keys():
            category_path = knowledge_dir / category
            if category_path.exists():
                for file in category_path.glob("**/*.json"):
                    knowledge_files[category].append({
                        "name": file.stem,
                        "path": str(file.relative_to(knowledge_dir))
                    })
        
        return templates.TemplateResponse(
            request,
            "knowledge_base.html",
            {"knowledge_files": knowledge_files}
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": str(e)}
        )


@app.get("/task/{task_id}/status")
async def task_status(task_id: str):
    """查詢任務進度 API"""
    task_queue = get_task_queue()
    status = task_queue.get_task_status(task_id)
    
    if not status:
        return {"error": "Task not found"}
    
    return status


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "backend": get_database_backend()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}",
            "backend": get_database_backend()
        }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", 8000))
    
    print("=" * 60)
    print("🚀 DSS Web UI 啟動中...")
    print(f"📍 主機：http://{host}:{port}")
    print(f"💾 資料庫：{get_database_backend()}")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port)
