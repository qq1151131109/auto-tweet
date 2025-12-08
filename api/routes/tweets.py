"""
推文生成API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from api.models import (
    TaskCreateResponse,
    TweetGenerationRequest,
    BatchTweetGenerationRequest
)
from api.auth import get_current_user_id
from storage import get_task_storage, TaskStatus
from tasks.tweet_tasks import generate_tweets_task, generate_batch_tweets_task
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=TaskCreateResponse)
async def generate_tweets(
    request: TweetGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成推文

    基于人设和日历生成指定数量的推文
    """
    storage = get_task_storage()

    # 验证必需参数
    if not request.persona_file:
        raise HTTPException(status_code=400, detail="persona_file is required")

    if not request.calendar_file and not request.auto_generate_calendar:
        raise HTTPException(
            status_code=400,
            detail="calendar_file is required or set auto_generate_calendar=true"
        )

    try:
        # 创建任务记录
        task_id = storage.create_task(
            task_type="tweets",
            user_id=user_id,
            input_params={
                "persona_file": request.persona_file,
                "calendar_file": request.calendar_file,
                "tweets_count": request.tweets_count,
                "temperature": request.temperature,
                "auto_generate_calendar": request.auto_generate_calendar,
                "enable_context": request.enable_context
            }
        )

        # 提交Celery任务
        generate_tweets_task.delay(
            task_id=task_id,
            persona_file=request.persona_file,
            calendar_file=request.calendar_file or "",
            tweets_count=request.tweets_count,
            temperature=request.temperature,
            auto_generate_calendar=request.auto_generate_calendar,
            enable_context=request.enable_context
        )

        logger.info(f"Tweet generation task created: {task_id}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=f"Tweet generation task submitted for {request.tweets_count} tweets"
        )

    except Exception as e:
        logger.error(f"Failed to create tweet generation task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post("/generate-batch", response_model=TaskCreateResponse)
async def generate_batch_tweets(
    request: BatchTweetGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    批量生成推文

    为多个人设并发生成推文
    """
    storage = get_task_storage()

    if len(request.persona_files) != len(request.calendar_files):
        raise HTTPException(
            status_code=400,
            detail="persona_files and calendar_files must have the same length"
        )

    try:
        # 创建任务记录
        task_id = storage.create_task(
            task_type="tweets_batch",
            user_id=user_id,
            input_params={
                "persona_files": request.persona_files,
                "calendar_files": request.calendar_files,
                "tweets_per_persona": request.tweets_per_persona,
                "temperature": request.temperature,
                "count": len(request.persona_files)
            }
        )

        # 提交Celery任务
        generate_batch_tweets_task.delay(
            task_id=task_id,
            persona_files=request.persona_files,
            calendar_files=request.calendar_files,
            tweets_per_persona=request.tweets_per_persona,
            temperature=request.temperature
        )

        logger.info(f"Batch tweet generation task created: {task_id}, personas: {len(request.persona_files)}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=f"Batch tweet generation task submitted for {len(request.persona_files)} personas"
        )

    except Exception as e:
        logger.error(f"Failed to create batch tweet task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
