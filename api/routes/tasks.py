"""
任务查询API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from api.models import TaskInfo, APIResponse
from api.auth import get_current_user_id
from storage import get_task_storage, TaskStatus
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{task_id}", response_model=TaskInfo)
async def get_task_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    查询任务状态

    获取任务的详细信息，包括状态、进度、结果等
    """
    storage = get_task_storage()

    task = storage.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证任务所有权（简单版本）
    # 生产环境应该严格验证user_id
    # if task.get("user_id") != user_id:
    #     raise HTTPException(status_code=403, detail="Access denied")

    return TaskInfo(**task)


@router.get("/", response_model=List[TaskInfo])
async def list_tasks(
    task_type: Optional[str] = Query(None, description="按类型过滤: persona | tweets | images"),
    status: Optional[TaskStatus] = Query(None, description="按状态过滤"),
    limit: int = Query(100, ge=1, le=500, description="最大返回数量"),
    user_id: str = Depends(get_current_user_id)
):
    """
    列出任务

    查询当前用户的任务列表，支持按类型和状态过滤
    """
    storage = get_task_storage()

    tasks = storage.list_tasks(
        user_id=user_id,
        task_type=task_type,
        status=status,
        limit=limit
    )

    return [TaskInfo(**task) for task in tasks]


@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除任务

    删除指定的任务记录
    """
    storage = get_task_storage()

    task = storage.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证任务所有权
    # if task.get("user_id") != user_id:
    #     raise HTTPException(status_code=403, detail="Access denied")

    success = storage.delete_task(task_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete task")

    return APIResponse(
        success=True,
        message=f"Task {task_id} deleted successfully"
    )


@router.post("/{task_id}/cancel", response_model=APIResponse)
async def cancel_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    取消任务

    尝试取消正在运行的任务
    """
    storage = get_task_storage()

    task = storage.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 只能取消pending或running状态的任务
    current_status = task.get("status")
    if current_status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in {current_status} status"
        )

    # 尝试撤销Celery任务
    try:
        from tasks.celery_app import celery_app
        celery_app.control.revoke(task_id, terminate=True)
    except Exception as e:
        logger.warning(f"Failed to revoke Celery task {task_id}: {e}")

    # 更新任务状态为cancelled
    storage.update_task(task_id, status=TaskStatus.CANCELLED)

    return APIResponse(
        success=True,
        message=f"Task {task_id} cancelled successfully"
    )
