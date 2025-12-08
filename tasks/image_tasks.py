"""
图片生成任务
"""
import asyncio
from celery import Task
from tasks.celery_app import celery_app
from storage import TaskStorage, TaskStatus, get_task_storage
from config import settings
import logging

logger = logging.getLogger(__name__)


class ImageGenerationTask(Task):
    """图片生成任务基类"""

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


@celery_app.task(bind=True, base=ImageGenerationTask, name='tasks.generate_images')
def generate_images_task(
    self,
    task_id: str,
    tweets_batch_file: str,
    output_dir: str = None,
    start_slot: int = 0,
    max_images: int = None,
    use_multi_gpu: bool = True
):
    """
    图片生成任务（支持进度更新）

    Args:
        task_id: 任务ID
        tweets_batch_file: 推文批次JSON文件路径
        output_dir: 输出目录
        start_slot: 起始slot
        max_images: 最大生成数量
        use_multi_gpu: 是否使用多GPU
    """
    storage = get_task_storage()

    try:
        # 更新状态为运行中
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        # 导入图片生成器
        from core.image_generator import ImageGenerationCoordinator

        # 创建协调器
        image_coord = ImageGenerationCoordinator(
            model_path=settings.zimage_model_path,
            num_gpus=settings.zimage_num_gpus,
            use_diffusers=settings.zimage_use_diffusers
        )

        # 设置输出目录
        if output_dir is None:
            output_dir = settings.image_output_dir

        logger.info(f"Task {task_id}: Starting image generation from {tweets_batch_file}")

        # 运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 生成图片
            results = loop.run_until_complete(
                image_coord.generate_from_tweets_batch(
                    tweets_batch_file=tweets_batch_file,
                    output_dir=output_dir,
                    start_slot=start_slot,
                    max_images=max_images,
                    use_multi_gpu=use_multi_gpu
                )
            )

            # 统计结果
            success_count = sum(1 for r in results if r.get("status") == "success")
            failed_count = len(results) - success_count

            logger.info(f"Task {task_id}: Image generation completed - {success_count} success, {failed_count} failed")

            # 更新进度为100%
            storage.update_task(task_id, progress=100)

            return {
                "total": len(results),
                "success": success_count,
                "failed": failed_count,
                "output_dir": output_dir,
                "results": results
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        raise


@celery_app.task(bind=True, base=ImageGenerationTask, name='tasks.generate_batch_images')
def generate_batch_images_task(
    self,
    task_id: str,
    tweets_batch_files: list[str],
    output_dir: str = None,
    use_multi_gpu: bool = True
):
    """
    批量图片生成任务

    Args:
        task_id: 任务ID
        tweets_batch_files: 多个推文批次JSON文件
        output_dir: 输出目录
        use_multi_gpu: 是否使用多GPU
    """
    storage = get_task_storage()

    try:
        storage.update_task(task_id, status=TaskStatus.RUNNING, progress=0)

        from core.image_generator import ImageGenerationCoordinator

        image_coord = ImageGenerationCoordinator(
            model_path=settings.zimage_model_path,
            num_gpus=settings.zimage_num_gpus,
            use_diffusers=settings.zimage_use_diffusers
        )

        if output_dir is None:
            output_dir = settings.image_output_dir

        logger.info(f"Task {task_id}: Batch generating images for {len(tweets_batch_files)} files")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        all_results = []

        try:
            total_files = len(tweets_batch_files)

            for i, tweets_file in enumerate(tweets_batch_files):
                logger.info(f"Task {task_id}: Processing file {i+1}/{total_files}")

                results = loop.run_until_complete(
                    image_coord.generate_from_tweets_batch(
                        tweets_batch_file=tweets_file,
                        output_dir=output_dir,
                        use_multi_gpu=use_multi_gpu
                    )
                )

                all_results.extend(results)

                # 更新进度
                progress = int((i + 1) / total_files * 100)
                storage.update_task(task_id, progress=progress)

            success_count = sum(1 for r in all_results if r.get("status") == "success")
            failed_count = len(all_results) - success_count

            logger.info(f"Task {task_id}: Batch image generation completed - {success_count} success, {failed_count} failed")

            return {
                "files_processed": total_files,
                "total_images": len(all_results),
                "success": success_count,
                "failed": failed_count,
                "output_dir": output_dir
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task {task_id}: Failed - {e}", exc_info=True)
        storage.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        raise
