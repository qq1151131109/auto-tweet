"""
人设生成任务
"""
import asyncio
from celery import Task
from tasks.celery_app import celery_app
from storage import TaskStorage, TaskStatus, get_task_storage
from config import settings
import logging

logger = logging.getLogger(__name__)


class PersonaGenerationTask(Task):
    """人设生成任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的回调"""
        storage = get_task_storage()
        storage.update_task(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(exc)
        )

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时的回调"""
        storage = get_task_storage()
        storage.update_task(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            progress=100,
            result=retval
        )


@celery_app.task(bind=True, base=PersonaGenerationTask, name='tasks.generate_persona')
def generate_persona_task(
    self,
    task_id: str,
    image_path: str,
    output_file: str,
    nsfw_level: str = "enabled",
    language: str = "English",
    location: str = "",
    business_goal: str = "",
    custom_instructions: str = "",
    temperature: float = 0.85
):
    """
    异步人设生成任务

    Args:
        task_id: 任务ID
        image_path: 图片路径
        output_file: 输出文件路径
        其他参数同 PersonaGenerator
    """
    storage = get_task_storage()

    try:
        # 更新任务状态为运行中
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        # 导入生成器（延迟导入避免循环依赖）
        from main import HighConcurrencyCoordinator

        # 创建协调器
        coordinator = HighConcurrencyCoordinator(
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
            max_concurrent=settings.llm_max_concurrent,
            weather_api_key=settings.weather_api_key
        )

        # 运行异步任务（在新的事件循环中）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info(f"Task {task_id}: Starting persona generation for {image_path}")

            # 调用人设生成
            persona = loop.run_until_complete(
                coordinator.generate_persona_from_image(
                    image_path=image_path,
                    output_file=output_file,
                    nsfw_level=nsfw_level,
                    language=language,
                    location=location,
                    business_goal=business_goal,
                    custom_instructions=custom_instructions,
                    temperature=temperature
                )
            )

            logger.info(f"Task {task_id}: Persona generation completed")

            # 返回结果
            return {
                "persona_name": persona.get("data", {}).get("name", "Unknown"),
                "output_file": output_file,
                "persona": persona
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=str(e)
        )
        raise


@celery_app.task(bind=True, base=PersonaGenerationTask, name='tasks.generate_batch_personas')
def generate_batch_personas_task(
    self,
    task_id: str,
    image_files: list[str],
    output_dir: str = "personas",
    nsfw_level: str = "enabled",
    language: str = "English"
):
    """
    批量人设生成任务

    Args:
        task_id: 任务ID
        image_files: 图片文件列表
        output_dir: 输出目录
        nsfw_level: NSFW级别
        language: 语言
    """
    storage = get_task_storage()

    try:
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        from main import HighConcurrencyCoordinator

        coordinator = HighConcurrencyCoordinator(
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
            max_concurrent=settings.llm_max_concurrent
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info(f"Task {task_id}: Starting batch persona generation for {len(image_files)} images")

            # 批量生成（会内部并发）
            loop.run_until_complete(
                coordinator.generate_batch_personas(
                    image_files=image_files,
                    output_dir=output_dir,
                    nsfw_level=nsfw_level,
                    language=language
                )
            )

            logger.info(f"Task {task_id}: Batch persona generation completed")

            return {
                "count": len(image_files),
                "output_dir": output_dir
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        raise
