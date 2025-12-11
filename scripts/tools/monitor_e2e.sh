#!/bin/bash
while true; do
    clear
    echo "=== 完整端到端测试监控 ==="
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    
    # 显示最新日志
    echo "=== 最新进度 (最后15行) ==="
    tail -15 test_e2e_full.log 2>/dev/null || echo "日志文件未找到"
    echo
    
    # 统计已生成图片
    echo "=== 已生成图片统计 ==="
    if [ -d "output_images_e2e" ]; then
        count=$(ls -1 output_images_e2e/*.png 2>/dev/null | wc -l)
        echo "已完成: $count/10 张"
        if [ $count -gt 0 ]; then
            echo
            echo "文件列表:"
            ls -lh output_images_e2e/*.png 2>/dev/null | tail -5
        fi
    else
        echo "输出目录不存在"
    fi
    
    echo
    echo "按 Ctrl+C 退出监控"
    
    sleep 10
done
