"""
API Pydantic模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime
from storage import TaskStatus


# ===== 通用响应模型 =====

class APIResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None


# ===== 任务相关模型 =====

class TaskInfo(BaseModel):
    """任务信息"""
    id: str
    type: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100, description="进度 0-100")
    user_id: Optional[str] = None
    input_params: dict
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreateResponse(BaseModel):
    """创建任务响应"""
    task_id: str
    status: TaskStatus
    message: str = "Task created successfully"


# ===== 人设生成相关模型 =====

class PersonaGenerationRequest(BaseModel):
    """人设生成请求"""
    image_url: Optional[str] = Field(None, description="图片URL（二选一）")
    image_base64: Optional[str] = Field(None, description="Base64编码的图片（二选一）")
    nsfw_level: str = Field("enabled", description="NSFW级别: enabled | disabled")
    language: str = Field("English", description="语言: English | 中文 | 日本語")
    location: str = Field("", description="地理位置（留空自动生成）")
    business_goal: str = Field("", description="业务目标")
    custom_instructions: str = Field("", description="自定义控制词")
    temperature: float = Field(0.85, ge=0.0, le=2.0, description="温度参数")


class BatchPersonaGenerationRequest(BaseModel):
    """批量人设生成请求"""
    image_urls: List[str] = Field(description="图片URL列表")
    nsfw_level: str = Field("enabled", description="NSFW级别")
    language: str = Field("English", description="语言")


# ===== 推文生成相关模型 =====

class TweetGenerationRequest(BaseModel):
    """推文生成请求"""
    persona_id: Optional[str] = Field(None, description="人设ID（如果已存在）")
    persona_file: Optional[str] = Field(None, description="人设文件路径")
    calendar_file: Optional[str] = Field(None, description="日历文件路径")
    tweets_count: int = Field(5, ge=1, le=100, description="推文数量")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="温度参数")
    auto_generate_calendar: bool = Field(False, description="是否自动生成日历")
    enable_context: bool = Field(False, description="是否启用上下文（天气等）")


class BatchTweetGenerationRequest(BaseModel):
    """批量推文生成请求"""
    persona_files: List[str] = Field(description="人设文件路径列表")
    calendar_files: List[str] = Field(description="日历文件路径列表")
    tweets_per_persona: int = Field(5, ge=1, le=100, description="每个人设的推文数")
    temperature: float = Field(1.0, description="温度参数")


# ===== 图片生成相关模型 =====

class ImageGenerationRequest(BaseModel):
    """图片生成请求"""
    tweets_batch_file: str = Field(description="推文批次JSON文件路径")
    output_dir: Optional[str] = Field(None, description="输出目录（默认output_images）")
    start_slot: int = Field(0, ge=0, description="起始slot")
    max_images: Optional[int] = Field(None, ge=1, description="最大生成数量")
    use_multi_gpu: bool = Field(True, description="是否使用多GPU")


class BatchImageGenerationRequest(BaseModel):
    """批量图片生成请求"""
    tweets_batch_files: List[str] = Field(description="推文批次JSON文件路径列表")
    output_dir: Optional[str] = Field(None, description="输出目录")
    use_multi_gpu: bool = Field(True, description="是否使用多GPU")


# ===== 健康检查模型 =====

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str = "1.0.0"
    redis_connected: bool
    celery_workers: int = 0
