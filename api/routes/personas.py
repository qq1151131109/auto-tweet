"""
人设生成API路由
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from api.models import (
    TaskCreateResponse,
    PersonaGenerationRequest,
    BatchPersonaGenerationRequest
)
from api.auth import get_current_user_id
from storage import get_task_storage, TaskStatus
from tasks.persona_tasks import generate_persona_task, generate_batch_personas_task
from pathlib import Path
import base64
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=TaskCreateResponse)
async def generate_persona(
    image: UploadFile = File(..., description="人设图片"),
    nsfw_level: str = Form("enabled"),
    language: str = Form("English"),
    location: str = Form(""),
    business_goal: str = Form(""),
    custom_instructions: str = Form(""),
    temperature: float = Form(0.85),
    user_id: str = Depends(get_current_user_id)
):
    """
    生成单个人设

    上传图片，生成完整的AI人设卡片
    """
    storage = get_task_storage()

    # 保存上传的图片
    image_id = str(uuid.uuid4())[:8]
    image_dir = Path("uploads/images")
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / f"{image_id}_{image.filename}"

    try:
        # 保存图片
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)

        # 创建输出文件路径
        output_file = f"personas/{image_id}_persona.json"

        # 创建任务记录
        task_id = storage.create_task(
            task_type="persona",
            user_id=user_id,
            input_params={
                "image_path": str(image_path),
                "output_file": output_file,
                "nsfw_level": nsfw_level,
                "language": language,
                "location": location,
                "business_goal": business_goal,
                "custom_instructions": custom_instructions,
                "temperature": temperature
            }
        )

        # 提交Celery任务
        generate_persona_task.delay(
            task_id=task_id,
            image_path=str(image_path),
            output_file=output_file,
            nsfw_level=nsfw_level,
            language=language,
            location=location,
            business_goal=business_goal,
            custom_instructions=custom_instructions,
            temperature=temperature
        )

        logger.info(f"Persona generation task created: {task_id}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Persona generation task submitted successfully"
        )

    except Exception as e:
        logger.error(f"Failed to create persona generation task: {e}", exc_info=True)
        # 清理上传的文件
        if image_path.exists():
            image_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post("/generate-batch", response_model=TaskCreateResponse)
async def generate_batch_personas(
    images: list[UploadFile] = File(..., description="多个人设图片"),
    nsfw_level: str = Form("enabled"),
    language: str = Form("English"),
    user_id: str = Depends(get_current_user_id)
):
    """
    批量生成人设

    上传多个图片，并发生成多个人设
    """
    storage = get_task_storage()

    # 保存所有图片
    image_paths = []
    image_dir = Path("uploads/images")
    image_dir.mkdir(parents=True, exist_ok=True)

    try:
        for image in images:
            image_id = str(uuid.uuid4())[:8]
            image_path = image_dir / f"{image_id}_{image.filename}"

            with open(image_path, "wb") as f:
                content = await image.read()
                f.write(content)

            image_paths.append(str(image_path))

        # 创建任务记录
        task_id = storage.create_task(
            task_type="persona_batch",
            user_id=user_id,
            input_params={
                "image_files": image_paths,
                "nsfw_level": nsfw_level,
                "language": language,
                "count": len(image_paths)
            }
        )

        # 提交Celery任务
        generate_batch_personas_task.delay(
            task_id=task_id,
            image_files=image_paths,
            output_dir="personas",
            nsfw_level=nsfw_level,
            language=language
        )

        logger.info(f"Batch persona generation task created: {task_id}, images: {len(image_paths)}")

        return TaskCreateResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=f"Batch persona generation task submitted for {len(image_paths)} images"
        )

    except Exception as e:
        logger.error(f"Failed to create batch persona task: {e}", exc_info=True)
        # 清理上传的文件
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
