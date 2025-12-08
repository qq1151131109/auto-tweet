"""
Celery应用配置
"""
from celery import Celery
from config import settings

# 创建Celery应用
celery_app = Celery(
    'tweet_generator',
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        'tasks.persona_tasks',
        'tasks.tweet_tasks',
        'tasks.image_tasks'
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务追踪
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,

    # 结果设置
    result_expires=3600 * 24,  # 结果保留24小时
    result_extended=True,  # 存储额外信息

    # 序列化
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # 时区
    timezone='UTC',
    enable_utc=True,

    # 任务优先级
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

__all__ = ['celery_app']
