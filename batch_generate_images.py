#!/usr/bin/env python3
"""
批量图片生成脚本 - 使用8卡并行处理多个推文批次

用法:
    python3 batch_generate_images.py output_full_pipeline/*_tweets.json
"""
import sys
from pathlib import Path

# 在导入其他模块前设置Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

zimage_path = project_root / "Z-Image" / "src"
if zimage_path.exists():
    sys.path.insert(0, str(zimage_path))

import subprocess
import time

def main():
    if len(sys.argv) < 2:
        print("用法: python3 batch_generate_images.py <tweet_batch_files>")
        sys.exit(1)

    tweet_files = sys.argv[1:]
    print(f"找到 {len(tweet_files)} 个推文批次文件")

    for tweet_file in tweet_files:
        if not Path(tweet_file).exists():
            print(f"跳过不存在的文件: {tweet_file}")
            continue

        print(f"\n{'='*60}")
        print(f"正在处理: {tweet_file}")
        print('='*60)

        # 使用main.py生成图片
        cmd = [
            "python3", "main.py",
            "--generate-images",
            "--tweets-batch", tweet_file,
            "--num-gpus", "8",
            "--use-native-pytorch"
        ]

        try:
            result = subprocess.run(cmd, check=True)
            print(f"✓ 完成: {tweet_file}")
        except subprocess.CalledProcessError as e:
            print(f"✗ 失败: {tweet_file} - {e}")
            continue

    print(f"\n{'='*60}")
    print("所有批次处理完成!")
    print('='*60)

if __name__ == "__main__":
    main()
