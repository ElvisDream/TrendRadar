import os
import shutil
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

def get_beijing_time():
    """获取北京时间"""
    tz_beijing = timezone(timedelta(hours=8))
    return datetime.now(tz_beijing)

def clean_old_output():
    """清理一周前的 output 文件夹内容"""
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ output 目录不存在。")
        return
    
    # 匹配文件夹名字例如 "2026年06月01日"
    pattern = re.compile(r"^(\d{4})年(\d{2})月(\d{2})日$")
    
    # 获取 7 天前的日期作为阈值
    threshold_date = get_beijing_time() - timedelta(days=7)
    threshold_str = threshold_date.strftime("%Y%m%d")
    
    print(f"🔍 开始检查，当前清理阈值为 7 天前: {threshold_date.strftime('%Y年%m月%d日')} 及之前的内容...")
    
    deleted_count = 0
    for item in output_dir.iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                folder_date_str = f"{match.group(1)}{match.group(2)}{match.group(3)}"
                if folder_date_str <= threshold_str:
                    print(f"🗑️ 发现过期文件夹，正在删除: {item}")
                    shutil.rmtree(item)
                    deleted_count += 1
    
    if deleted_count == 0:
        print("✅ 没有需要清理的旧内容。")
    else:
        print(f"✅ 成功清理了 {deleted_count} 个过期文件夹。")

if __name__ == "__main__":
    clean_old_output()
