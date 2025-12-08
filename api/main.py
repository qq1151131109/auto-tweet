"""
FastAPI主应用
AI Tweet Generator API
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 Starting AI Tweet Generator API...")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Debug: {settings.debug}")
    logger.info(f"   Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"   LLM API: {settings.llm_api_base}")
    logger.info(f"   LLM Model: {settings.llm_model}")

    yield

    # 关闭时执行
    logger.info("👋 Shutting down AI Tweet Generator API...")


# 创建FastAPI应用
app = FastAPI(
    title="AI Tweet Generator API",
    description="Generate AI personas, tweets, and images at scale with async task processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS中间件（允许跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常捕获"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


# 导入路由
from api.routes import personas, tweets, images, tasks as tasks_routes

# 注册路由
app.include_router(personas.router, prefix="/api/v1/personas", tags=["Personas"])
app.include_router(tweets.router, prefix="/api/v1/tweets", tags=["Tweets"])
app.include_router(images.router, prefix="/api/v1/images", tags=["Images"])
app.include_router(tasks_routes.router, prefix="/api/v1/tasks", tags=["Tasks"])


# 健康检查端点
@app.get("/health", tags=["System"])
async def health_check():
    """健康检查"""
    from api.models import HealthCheckResponse
    import redis

    # 检查Redis连接
    redis_connected = False
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_connected = True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    # 检查Celery workers（简单版本）
    celery_workers = 0
    try:
        from tasks.celery_app import celery_app
        stats = celery_app.control.inspect().stats()
        if stats:
            celery_workers = len(stats)
    except Exception as e:
        logger.warning(f"Celery inspection failed: {e}")

    return HealthCheckResponse(
        status="healthy",
        redis_connected=redis_connected,
        celery_workers=celery_workers
    )


# 根路径
@app.get("/", tags=["System"])
async def root():
    """API根路径"""
    return {
        "name": "AI Tweet Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.api_workers
    )
