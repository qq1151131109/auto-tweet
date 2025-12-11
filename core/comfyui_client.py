"""
ComfyUI API 客户端
支持并发调用多个 ComfyUI 实例（端口 9000-9003）
"""
import asyncio
import aiohttp
import json
import uuid
import websockets
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI API 客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:9000"):
        """
        初始化 ComfyUI 客户端

        Args:
            base_url: ComfyUI 服务地址，如 http://127.0.0.1:9000
        """
        self.base_url = base_url
        self.client_id = str(uuid.uuid4())

    async def queue_prompt(self, workflow: Dict) -> str:
        """
        提交工作流到队列

        Args:
            workflow: ComfyUI 工作流 JSON

        Returns:
            prompt_id: 任务ID
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "prompt": workflow,
                "client_id": self.client_id
            }

            async with session.post(f"{self.base_url}/prompt", json=data) as response:
                result = await response.json()
                return result['prompt_id']

    async def get_history(self, prompt_id: str) -> Optional[Dict]:
        """获取任务历史记录"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/history/{prompt_id}") as response:
                history = await response.json()
                return history.get(prompt_id)

    async def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """下载生成的图片"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/view"
            params = {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type
            }
            async with session.get(url, params=params) as response:
                return await response.read()

    async def wait_for_completion(self, prompt_id: str, timeout: int = 600) -> Dict:
        """
        等待任务完成

        Args:
            prompt_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            生成结果信息
        """
        ws_url = f"ws://{self.base_url.split('//')[1]}/ws?clientId={self.client_id}"

        async with websockets.connect(ws_url) as websocket:
            start_time = asyncio.get_event_loop().time()

            while True:
                # 检查超时
                if asyncio.get_event_loop().time() - start_time > timeout:
                    raise TimeoutError(f"任务 {prompt_id} 超时")

                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    msg_data = json.loads(message)

                    # 检查是否是我们的任务
                    if msg_data.get('type') == 'executing':
                        data = msg_data.get('data', {})
                        if data.get('prompt_id') == prompt_id and data.get('node') is None:
                            # 任务完成
                            history = await self.get_history(prompt_id)
                            return history

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"WebSocket 错误: {e}")
                    break

        # 如果 WebSocket 失败，轮询检查
        for _ in range(timeout):
            history = await self.get_history(prompt_id)
            if history:
                return history
            await asyncio.sleep(1)

        raise TimeoutError(f"任务 {prompt_id} 超时")

    async def generate_image(
        self,
        workflow: Dict,
        output_dir: str = "output_images",
        filename_prefix: str = "comfyui"
    ) -> Dict:
        """
        生成图片（完整流程）

        Args:
            workflow: ComfyUI 工作流
            output_dir: 输出目录
            filename_prefix: 文件名前缀

        Returns:
            结果字典，包含 output_path, prompt_id 等
        """
        # 提交任务
        prompt_id = await self.queue_prompt(workflow)
        logger.info(f"✓ 任务已提交: {prompt_id}")

        # 等待完成
        history = await self.wait_for_completion(prompt_id)
        logger.info(f"✓ 任务完成: {prompt_id}")

        # 获取输出图片
        outputs = history.get('outputs', {})
        images = []
        all_image_infos = []  # 收集所有图片信息

        # 首先收集所有图片信息
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for image_info in node_output['images']:
                    all_image_infos.append(image_info)

        # 如果有多张图片(多阶段生成),只保存最后一张(文件名最新的)
        # 工作流中有3个输出节点:337(stage1), 210(stage2), 307(stage3)
        # 我们只需要307的最终结果
        if all_image_infos:
            # 按文件名排序,取最后一个(ComfyUI按时间顺序命名)
            image_info = sorted(all_image_infos, key=lambda x: x['filename'])[-1]

            # 下载图片
            image_data = await self.get_image(
                filename=image_info['filename'],
                subfolder=image_info.get('subfolder', ''),
                folder_type=image_info.get('type', 'output')
            )

            # 保存到本地
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"{filename_prefix}_{timestamp}.png"
            local_path = output_path / local_filename

            with open(local_path, 'wb') as f:
                f.write(image_data)

            images.append(str(local_path))
            logger.info(f"✓ 图片已保存: {local_path} ({image_info['filename']})")

        return {
            "prompt_id": prompt_id,
            "images": images,
            "status": "success"
        }


class ComfyUIPool:
    """ComfyUI 实例池（支持并发）"""

    def __init__(self, ports: List[int] = [9000, 9001, 9002, 9003], host: str = "127.0.0.1"):
        """
        初始化 ComfyUI 实例池

        Args:
            ports: ComfyUI 端口列表
            host: ComfyUI 主机地址
        """
        self.clients = [
            ComfyUIClient(base_url=f"http://{host}:{port}")
            for port in ports
        ]
        self.semaphore = asyncio.Semaphore(len(self.clients))
        logger.info(f"🔧 初始化 ComfyUI 实例池: {len(self.clients)} 个实例")

    async def generate_image(self, workflow: Dict, **kwargs) -> Dict:
        """
        使用池中的客户端生成图片（自动负载均衡）
        """
        async with self.semaphore:
            # 随机选择一个客户端（简单的负载均衡）
            client = random.choice(self.clients)
            return await client.generate_image(workflow, **kwargs)

    async def generate_batch(
        self,
        workflows: List[Dict],
        output_dir: str = "output_images",
        filename_prefix: str = "comfyui"
    ) -> List[Dict]:
        """
        批量并发生成图片

        Args:
            workflows: 工作流列表
            output_dir: 输出目录
            filename_prefix: 文件名前缀

        Returns:
            结果列表
        """
        tasks = [
            self.generate_image(workflow, output_dir=output_dir, filename_prefix=f"{filename_prefix}_{i}")
            for i, workflow in enumerate(workflows)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 工作流 {i} 失败: {result}")
                final_results.append({
                    "status": "failed",
                    "error": str(result)
                })
            else:
                final_results.append(result)

        return final_results


def load_workflow_template(template_path: str = "workflow/zimage-121101.json") -> Dict:
    """加载工作流模板"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_workflow_prompt(
    workflow: Dict,
    positive_prompt: str,
    negative_prompt: str = "",
    trigger_word: str = "",
    quality_words: str = "",
    lora_path: str = "",
    lora_strength: float = 1.0,
    seed: Optional[int] = None
) -> Dict:
    """
    更新工作流中的提示词和参数（适配 zimage-api-121102 格式）

    Args:
        workflow: 工作流模板
        positive_prompt: 正向提示词（场景描述）
        negative_prompt: 负向提示词
        trigger_word: LoRA 触发词
        quality_words: 画质词（如 "photorealistic, detailed, high quality"）
        lora_path: LoRA 完整文件路径（如 "lora/character.safetensors"）
        lora_strength: LoRA 强度
        seed: 随机种子

    Returns:
        更新后的工作流
    """
    import copy
    workflow = copy.deepcopy(workflow)

    # 组装完整正向提示词：触发词 + 场景描述 + 画质词
    prompt_parts = []
    if trigger_word:
        prompt_parts.append(trigger_word.strip())
    if positive_prompt:
        prompt_parts.append(positive_prompt.strip())
    if quality_words:
        prompt_parts.append(quality_words.strip())

    full_prompt = ', '.join(prompt_parts)

    # 更新正向提示词（节点6 - CLIPTextEncode）
    if '6' in workflow:
        workflow['6']['inputs']['text'] = full_prompt
        logger.info(f"✓ 更新正向提示词 (节点6): {full_prompt[:80]}...")

    # 保持负向提示词不变（使用工作流中的默认值）
    # 工作流中已包含优化好的中文负向提示词，无需修改

    # 更新 LoRA（节点343 - LorapathLoader）
    if '343' in workflow:
        if lora_path:
            # LorapathLoader 节点需要分开 lora_path (目录) 和 lora_name (文件名)
            # 输入: "lora/hollyjai.safetensors" → 拆分为目录和文件名
            # 重要: 必须转换为绝对路径,因为ComfyUI的工作目录和项目目录不同
            import os

            # 如果是相对路径,转换为绝对路径
            if not os.path.isabs(lora_path):
                # 从项目根目录解析相对路径
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                lora_path = os.path.join(project_root, lora_path)

            # 解析符号链接到实际文件
            lora_path = os.path.realpath(lora_path)

            lora_dir = os.path.dirname(lora_path)  # 绝对路径目录
            lora_file = os.path.basename(lora_path)  # 文件名

            workflow['343']['inputs']['lora_path'] = lora_dir
            workflow['343']['inputs']['lora_name'] = lora_file
            workflow['343']['inputs']['strength_model'] = lora_strength
            workflow['343']['inputs']['strength_clip'] = lora_strength
            logger.info(f"✓ 更新 LoRA (节点343): {lora_dir}/{lora_file} (强度 {lora_strength})")
        else:
            # 不使用 LoRA 时清空所有字段
            workflow['343']['inputs']['lora_path'] = ""
            workflow['343']['inputs']['lora_name'] = ""
            logger.info("✓ 未指定 LoRA，已清空 LoRA 配置")

    # 更新种子
    if seed is not None:
        # 阶段1种子（节点322）
        if '322' in workflow:
            workflow['322']['inputs']['seed'] = seed
        # 阶段2种子（节点226）
        if '226' in workflow:
            workflow['226']['inputs']['seed'] = seed + 1
        # 阶段3种子（节点305）
        if '305' in workflow:
            workflow['305']['inputs']['seed'] = seed + 2
        logger.info(f"✓ 更新种子: stage1={seed}, stage2={seed+1}, stage3={seed+2}")

    return workflow
