"""文件锁工具（支持跨平台）"""
import os
import time
import fcntl
import errno
from contextlib import contextmanager
from typing import Optional


class FileLock:
    """文件锁实现（使用 fcntl 进行原子锁定）"""

    def __init__(self, lock_file: str, timeout: float = 10.0, check_interval: float = 0.05):
        """
        初始化文件锁

        Args:
            lock_file: 锁文件路径
            timeout: 获取锁的超时时间（秒）
            check_interval: 检查间隔（秒）
        """
        self.lock_file = lock_file
        self.timeout = timeout
        self.check_interval = check_interval
        self.fd: Optional[int] = None

    def acquire(self) -> bool:
        """
        获取文件锁

        Returns:
            是否成功获取锁
        """
        start_time = time.time()

        # 确保锁文件目录存在
        lock_dir = os.path.dirname(self.lock_file)
        if lock_dir and not os.path.exists(lock_dir):
            os.makedirs(lock_dir, exist_ok=True)

        while True:
            try:
                # 打开或创建锁文件
                self.fd = os.open(self.lock_file, os.O_CREAT | os.O_WRONLY)

                # 尝试获取排他锁（非阻塞）
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                # 写入当前进程ID和时间戳
                os.write(self.fd, f"{os.getpid()}:{time.time()}\n".encode())
                os.fsync(self.fd)

                return True

            except (IOError, OSError) as e:
                # 如果锁已被占用
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    if self.fd is not None:
                        os.close(self.fd)
                        self.fd = None

                    # 检查是否超时
                    if time.time() - start_time >= self.timeout:
                        raise TimeoutError(f"无法在 {self.timeout} 秒内获取文件锁: {self.lock_file}")

                    # 等待后重试
                    time.sleep(self.check_interval)
                else:
                    # 其他错误直接抛出
                    if self.fd is not None:
                        os.close(self.fd)
                        self.fd = None
                    raise

    def release(self):
        """释放文件锁"""
        if self.fd is not None:
            try:
                # 释放锁
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
            except Exception as e:
                print(f"[FileLock] 释放锁时出错: {e}")
            finally:
                self.fd = None

            # 删除锁文件
            try:
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
            except Exception as e:
                print(f"[FileLock] 删除锁文件时出错: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.release()


@contextmanager
def file_lock(file_path: str, timeout: float = 10.0):
    """
    文件锁上下文管理器（便捷接口）

    使用方式:
        with file_lock("/path/to/file.json"):
            # 读写文件操作
            pass

    Args:
        file_path: 要锁定的文件路径
        timeout: 超时时间（秒）
    """
    lock_file = f"{file_path}.lock"
    lock = FileLock(lock_file, timeout=timeout)

    try:
        lock.acquire()
        yield lock
    finally:
        lock.release()
