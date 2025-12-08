"""
图片生成API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from api.models import (
    TaskCreateResponse,
    ImageGenerationRequest,
    BatchImageGenerationRequest
)
from api.auth import get_current_user_id
from storage import get_task_storage, TaskStatus
from tasks.image_tasks import generate_images_task, generate_batch_images_task
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=TaskCreateResponse)
async def generate_images(
    request: ImageGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    生成图片

    基于推文批次JSON生成AI图片（支持多GPU加速）
    """
    storage = get_task_storage()

    try:
        # 创建任务记录
        task_id = storage.create_task(
            task_type="images",
            user_id=user_id,
            input_params={
                "tweets_batch_file": request.tweets_batch_file,
                "output_dir": request.output_dir,
                "start_slot": request.start_slot,
                "max_images": request.max_images,
                "use_multi_gpu": request.use_multi_gpu
            }
        )

        # 提交Celery任务
        generate_images_task.delay(
            task_id=task_id,
            tweets_batch_file=request.tweets_batch_file,
            output_dir=request.output_dir,
            start_slot=request.start_slot,
            max_images=request.max_images,
            use_multi_gpu=request.use_multi_gpu
        )

        logger.info(f"Image generation task created: {task_id}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Image generation task submitted successfully. This may take a while (up to 1 hour for large batches)"
        )

    except Exception as e:
        logger.error(f"Failed to create image generation task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post("/generate-batch", response_model=TaskCreateResponse)
async def generate_batch_images(
    request: BatchImageGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    批量生成图片

    为多个推文批次文件生成图片
    """
    storage = get_task_storage()

    try:
        # 创建任务记录
        task_id = storage.create_task(
            task_type="images_batch",
            user_id=user_id,
            input_params={
                "tweets_batch_files": request.tweets_batch_files,
                "output_dir": request.output_dir,
                "use_multi_gpu": request.use_multi_gpu,
                "count": len(request.tweets_batch_files)
            }
        )

        # 提交Celery任务
        generate_batch_images_task.delay(
            task_id=task_id,
            tweets_batch_files=request.tweets_batch_files,
            output_dir=request.output_dir,
            use_multi_gpu=request.use_multi_gpu
        )

        logger.info(f"Batch image generation task created: {task_id}, files: {len(request.tweets_batch_files)}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=f"Batch image generation task submitted for {len(request.tweets_batch_files)} files"
        )

    except Exception as e:
        logger.error(f"Failed to create batch image task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
