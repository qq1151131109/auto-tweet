"""
配置管理 - 统一的环境配置
支持从环境变量和.env文件读取
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # ===== 环境配置 =====
    environment: str = "development"  # development | staging | production
    debug: bool = True

    # ===== API服务配置 =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # ===== Redis配置 =====
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    @property
    def redis_url(self) -> str:
        """构建Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ===== Celery配置 =====
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 3600  # 1小时超时

    @property
    def celery_broker(self) -> str:
        """Celery broker URL（默认使用Redis）"""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        """Celery result backend（默认使用Redis）"""
        return self.celery_result_backend or self.redis_url

    # ===== LLM API配置 =====
    llm_api_key: str
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4"
    llm_max_concurrent: int = 20
    llm_temperature: float = 1.0

    # ===== 天气API配置 =====
    weather_api_key: Optional[str] = None

    # ===== Z-Image配置 =====
    zimage_model_path: str = "Z-Image/ckpts/Z-Image-Turbo"
    zimage_num_gpus: Optional[int] = None  # None=自动检测
    zimage_use_diffusers: bool = True

    # ===== 存储配置 =====
    output_dir: str = "output_standalone"
    image_output_dir: str = "output_images"
    persona_dir: str = "personas"
    calendar_dir: str = "calendars"
    task_storage_dir: str = "task_storage"  # 任务状态存储目录

    # ===== API Key鉴权配置 =====
    # 简单版本：预定义的API keys（生产环境应该用数据库）
    api_keys: str = "demo-key-1,demo-key-2,demo-key-3"  # 逗号分隔

    @property
    def valid_api_keys(self) -> set:
        """获取有效的API keys集合"""
        return set(key.strip() for key in self.api_keys.split(',') if key.strip())

    # ===== 限流配置 =====
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # ===== 日志配置 =====
    log_level: str = "INFO"
    log_format: str = "json"  # json | text

    # ===== 生成配置文件路径 =====
    generation_config_file: Optional[str] = None  # 生成配置文件路径（YAML/JSON）

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

        # 支持从环境变量读取，前缀为空
        env_prefix = ""

    def load_generation_config(self):
        """
        加载生成配置

        Returns:
            GenerationConfig: 生成配置实例
        """
        from config.generation import GenerationConfig, load_generation_config

        if self.generation_config_file:
            return load_generation_config(self.generation_config_file)

        # 尝试从默认位置加载（优先根目录，然后config目录）
        default_paths = [
            "generation_config.yaml",           # 用户自定义配置（根目录）
            "generation_config.json",           # 用户自定义配置（根目录）
            "config/default.yaml",              # 默认配置
            "config/default.json",              # 默认配置
        ]
        for path in default_paths:
            if os.path.exists(path):
                return load_generation_config(path)

        # 使用默认配置
        return GenerationConfig()


# 全局配置实例
settings = Settings()


# 导出常用配置
__all__ = ['settings', 'Settings']
