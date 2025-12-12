"""
Multi-GPU Image Generator - Parallel generation across multiple GPUs

Uses torch.multiprocessing to distribute image generation tasks across multiple GPUs.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import multiprocessing as mp
from queue import Empty
import time

import torch
from PIL import Image
from loguru import logger


class GPUWorker:
    """Worker process for a single GPU"""

    def __init__(self, gpu_id: int, task_queue: mp.Queue, result_queue: mp.Queue):
        """
        Initialize GPU worker.

        Args:
            gpu_id: GPU device ID
            task_queue: Queue for receiving tasks
            result_queue: Queue for sending results
        """
        self.gpu_id = gpu_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.generator = None
        self.current_lora = None

    def run(self):
        """Main worker loop - processes tasks from queue"""
        # Import NativeImageGenerator here (after path setup in worker_process)
        from core.native_image_generator import NativeImageGenerator

        # Set this process to use specific GPU
        os.environ['CUDA_VISIBLE_DEVICES'] = str(self.gpu_id)
        torch.cuda.set_device(0)  # After setting CUDA_VISIBLE_DEVICES, use device 0

        logger.info(f"[GPU {self.gpu_id}] Worker started")

        # Initialize generator once
        self.generator = NativeImageGenerator(device='cuda:0')

        while True:
            try:
                # Get task from queue (timeout to allow checking for shutdown)
                task = self.task_queue.get(timeout=1)

                if task is None:  # Poison pill to shutdown
                    logger.info(f"[GPU {self.gpu_id}] Shutdown signal received")
                    break

                # Process task
                result = self._process_task(task)
                self.result_queue.put(result)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"[GPU {self.gpu_id}] Worker error: {e}")
                self.result_queue.put({
                    'success': False,
                    'task_id': task.get('task_id', -1),
                    'error': str(e)
                })

        # Cleanup
        if self.generator:
            self.generator.unload()

        logger.info(f"[GPU {self.gpu_id}] Worker stopped")

    def _process_task(self, task: Dict) -> Dict:
        """
        Process a single image generation task.

        Args:
            task: Task dict with keys: task_id, prompt, lora_path, lora_strength, seed, output_path

        Returns:
            Result dict with success status
        """
        task_id = task['task_id']
        prompt = task['prompt']
        lora_path = task.get('lora_path')
        lora_strength = task.get('lora_strength', 0.8)
        seed = task.get('seed')
        output_path = task.get('output_path')

        logger.info(f"[GPU {self.gpu_id}] Processing task {task_id}")

        start_time = time.time()

        try:
            # Load LoRA if specified and different from current
            if lora_path and lora_path != self.current_lora:
                if self.current_lora:
                    self.generator.lora_manager.unload_lora()

                logger.info(f"[GPU {self.gpu_id}] Loading LoRA: {lora_path}")
                self.generator.lora_manager.load_lora(lora_path, lora_strength)
                self.current_lora = lora_path
            elif not lora_path and self.current_lora:
                # Unload LoRA if task doesn't need it
                self.generator.lora_manager.unload_lora()
                self.current_lora = None

            # Generate image (don't pass lora_path since we already loaded it)
            image = self.generator.generate(
                prompt=prompt,
                progressive=True,
                seed=seed,
                lora_path=None  # Already loaded above
            )

            # Save image
            if output_path:
                # Ensure directory exists
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                image.save(output_path)

            elapsed = time.time() - start_time

            logger.success(f"[GPU {self.gpu_id}] Task {task_id} complete ({elapsed:.1f}s)")

            return {
                'success': True,
                'task_id': task_id,
                'output_path': output_path,
                'elapsed': elapsed
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[GPU {self.gpu_id}] Task {task_id} failed: {e}")

            return {
                'success': False,
                'task_id': task_id,
                'error': str(e),
                'elapsed': elapsed
            }


def worker_process(gpu_id: int, task_queue: mp.Queue, result_queue: mp.Queue):
    """Entry point for worker process - handles path setup before imports"""
    import sys
    from pathlib import Path

    # CRITICAL: Setup paths BEFORE importing any project modules
    # Worker process starts fresh and needs Z-Image in path
    project_root = Path(__file__).parent.parent
    zimage_path = project_root / "Z-Image" / "src"
    if zimage_path.exists() and str(zimage_path) not in sys.path:
        sys.path.insert(0, str(zimage_path))

    # Also add project root
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    worker = GPUWorker(gpu_id, task_queue, result_queue)
    worker.run()


class MultiGPUImageGenerator:
    """
    Multi-GPU parallel image generator.

    Distributes image generation tasks across multiple GPUs using process pools.
    """

    def __init__(self, num_gpus: int = None, gpu_ids: List[int] = None):
        """
        Initialize multi-GPU generator.

        Args:
            num_gpus: Number of GPUs to use (default: all available)
            gpu_ids: Specific GPU IDs to use (overrides num_gpus)
        """
        if gpu_ids:
            self.gpu_ids = gpu_ids
        elif num_gpus:
            self.gpu_ids = list(range(num_gpus))
        else:
            self.gpu_ids = list(range(torch.cuda.device_count()))

        if not self.gpu_ids:
            raise RuntimeError("No GPUs available")

        logger.info(f"Initializing MultiGPUImageGenerator with GPUs: {self.gpu_ids}")

        self.num_gpus = len(self.gpu_ids)
        self.task_queue = None
        self.result_queue = None
        self.workers = []

    def start(self):
        """Start worker processes"""
        # Use 'spawn' to avoid CUDA initialization issues
        mp.set_start_method('spawn', force=True)

        self.task_queue = mp.Queue()
        self.result_queue = mp.Queue()

        # Start worker processes
        for gpu_id in self.gpu_ids:
            p = mp.Process(
                target=worker_process,
                args=(gpu_id, self.task_queue, self.result_queue)
            )
            p.start()
            self.workers.append(p)

        logger.info(f"Started {len(self.workers)} worker processes")

    def generate_batch(
        self,
        tasks: List[Dict],
        timeout: int = 600
    ) -> List[Dict]:
        """
        Generate images for a batch of tasks in parallel.

        Args:
            tasks: List of task dicts with keys: prompt, lora_path, lora_strength, seed, output_path
            timeout: Max time to wait for all tasks (seconds)

        Returns:
            List of result dicts
        """
        if not self.workers:
            self.start()

        # Add task_id to each task
        for idx, task in enumerate(tasks):
            task['task_id'] = idx

        # Submit all tasks to queue
        for task in tasks:
            self.task_queue.put(task)

        logger.info(f"Submitted {len(tasks)} tasks to {self.num_gpus} GPUs")

        # Collect results
        results = []
        start_time = time.time()

        while len(results) < len(tasks):
            if time.time() - start_time > timeout:
                logger.error(f"Timeout waiting for results ({timeout}s)")
                break

            try:
                result = self.result_queue.get(timeout=1)
                results.append(result)

                success_count = sum(1 for r in results if r['success'])
                logger.info(f"Progress: {len(results)}/{len(tasks)} ({success_count} success)")

            except Empty:
                continue

        # Sort results by task_id
        results.sort(key=lambda x: x['task_id'])

        return results

    def shutdown(self):
        """Shutdown all worker processes"""
        if not self.workers:
            return

        logger.info("Shutting down workers...")

        # Send poison pills
        for _ in self.workers:
            self.task_queue.put(None)

        # Wait for workers to finish
        for p in self.workers:
            p.join(timeout=10)
            if p.is_alive():
                logger.warning(f"Force terminating worker {p.pid}")
                p.terminate()

        self.workers = []
        logger.info("All workers stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
