"""
推文生成任务
"""
import asyncio
from celery import Task
from tasks.celery_app import celery_app
from storage import TaskStorage, TaskStatus, get_task_storage
from config import settings
import logging

logger = logging.getLogger(__name__)


class TweetGenerationTask(Task):
    """推文生成任务基类"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        storage = get_task_storage()
        storage.update_task(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=str(exc)
        )

    def on_success(self, retval, task_id, args, kwargs):
        storage = get_task_storage()
        storage.update_task(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            progress=100,
            result=retval
        )


@celery_app.task(bind=True, base=TweetGenerationTask, name='tasks.generate_tweets')
def generate_tweets_task(
    self,
    task_id: str,
    persona_file: str,
    calendar_file: str,
    tweets_count: int = 5,
    temperature: float = 1.0,
    auto_generate_calendar: bool = False,
    enable_context: bool = False
):
    """
    推文生成任务

    Args:
        task_id: 任务ID
        persona_file: 人设文件路径
        calendar_file: 日历文件路径
        tweets_count: 推文数量
        temperature: 温度参数
        auto_generate_calendar: 是否自动生成日历
        enable_context: 是否启用上下文（天气等）
    """
    storage = get_task_storage()

    try:
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        from main import HighConcurrencyCoordinator

        coordinator = HighConcurrencyCoordinator(
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
            max_concurrent=settings.llm_max_concurrent,
            weather_api_key=settings.weather_api_key,
            output_dir=settings.output_dir
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info(f"Task {task_id}: Generating {tweets_count} tweets")

            tweets_batch = loop.run_until_complete(
                coordinator.generate_tweets_for_persona(
                    persona_file=persona_file,
                    calendar_file=calendar_file,
                    tweets_count=tweets_count,
                    temperature=temperature,
                    auto_generate_calendar=auto_generate_calendar,
                    enable_context=enable_context
                )
            )

            logger.info(f"Task {task_id}: Tweet generation completed")

            return {
                "persona_name": tweets_batch.get("persona", {}).get("name", "Unknown"),
                "tweet_count": len(tweets_batch.get("tweets", [])),
                "tweets_batch": tweets_batch
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        raise


@celery_app.task(bind=True, base=TweetGenerationTask, name='tasks.generate_batch_tweets')
def generate_batch_tweets_task(
    self,
    task_id: str,
    persona_files: list[str],
    calendar_files: list[str],
    tweets_per_persona: int = 5,
    temperature: float = 1.0
):
    """
    批量推文生成任务

    Args:
        task_id: 任务ID
        persona_files: 人设文件列表
        calendar_files: 日历文件列表
        tweets_per_persona: 每个人设的推文数
        temperature: 温度参数
    """
    storage = get_task_storage()

    try:
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        from main import HighConcurrencyCoordinator

        coordinator = HighConcurrencyCoordinator(
            api_key=settings.llm_api_key,
            api_base=settings.llm_api_base,
            model=settings.llm_model,
            max_concurrent=settings.llm_max_concurrent,
            output_dir=settings.output_dir
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            logger.info(f"Task {task_id}: Batch generating tweets for {len(persona_files)} personas")

            loop.run_until_complete(
                coordinator.generate_batch_tweets(
                    persona_files=persona_files,
                    calendar_files=calendar_files,
                    tweets_per_persona=tweets_per_persona,
                    temperature=temperature
                )
            )

            logger.info(f"Task {task_id}: Batch tweet generation completed")

            return {
                "persona_count": len(persona_files),
                "tweets_per_persona": tweets_per_persona
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        raise
