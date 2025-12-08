"""
任务状态存储 - 简单的JSON文件存储
后续可以升级到PostgreSQL/MongoDB
"""
import json
import uuid
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
import threading


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStorage:
    """任务存储管理器 - 线程安全的JSON文件存储"""

    def __init__(self, storage_dir: str = "task_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _get_task_file(self, task_id: str) -> Path:
        """获取任务文件路径"""
        return self.storage_dir / f"{task_id}.json"

    def create_task(
        self,
        task_type: str,
        input_params: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """
        创建新任务

        Args:
            task_type: 任务类型（persona | tweets | images）
            input_params: 输入参数
            user_id: 用户ID（可选）

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        task_data = {
            "id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "user_id": user_id,
            "input_params": input_params,
            "progress": 0,
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
        }

        with self._lock:
            task_file = self._get_task_file(task_id)
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)

        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        task_file = self._get_task_file(task_id)

        if not task_file.exists():
            return None

        with self._lock:
            with open(task_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度（0-100）
            result: 结果数据
            error: 错误信息

        Returns:
            是否更新成功
        """
        task = self.get_task(task_id)
        if not task:
            return False

        # 更新字段
        if status is not None:
            task["status"] = status

            # 自动设置时间戳
            if status == TaskStatus.RUNNING and not task.get("started_at"):
                task["started_at"] = datetime.now().isoformat()
            elif status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task["completed_at"] = datetime.now().isoformat()

        if progress is not None:
            task["progress"] = min(100, max(0, progress))

        if result is not None:
            task["result"] = result

        if error is not None:
            task["error"] = error

        # 保存
        with self._lock:
            task_file = self._get_task_file(task_id)
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, ensure_ascii=False, indent=2)

        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        task_file = self._get_task_file(task_id)

        if not task_file.exists():
            return False

        with self._lock:
            task_file.unlink()

        return True

    def list_tasks(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        列出任务

        Args:
            user_id: 按用户ID过滤
            task_type: 按任务类型过滤
            status: 按状态过滤
            limit: 最大数量

        Returns:
            任务列表
        """
        tasks = []

        with self._lock:
            for task_file in self.storage_dir.glob("*.json"):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task = json.load(f)

                    # 应用过滤条件
                    if user_id and task.get("user_id") != user_id:
                        continue
                    if task_type and task.get("type") != task_type:
                        continue
                    if status and task.get("status") != status:
                        continue

                    tasks.append(task)

                    if len(tasks) >= limit:
                        break

                except Exception:
                    continue

        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)

        return tasks


# 全局单例
_task_storage = None


def get_task_storage() -> TaskStorage:
    """获取任务存储单例"""
    global _task_storage
    if _task_storage is None:
        from config import settings
        _task_storage = TaskStorage(storage_dir=settings.task_storage_dir)
    return _task_storage
