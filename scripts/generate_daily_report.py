#!/usr/bin/env python3
"""
为 OpenClaw 生成每日汇报内容 (Markdown)。
可输出到 stdout 或文件，便于 cron 任务推送到聊天群。
"""

import os
import json
from datetime import datetime, timedelta
import email.utils
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'prompt_library.json')
GITHUB_PAGE = "https://yangyuwen-bri.github.io/seedance-prompt-library/"
GITHUB_REPO = "https://github.com/yangyuwen-bri/seedance-prompt-library"

def parse_twitter_date(date_str):
    """解析 Twitter 时间格式: Tue Feb 10 22:25:40 +0000 2026"""
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except:
        return datetime.min.replace(tzinfo=None)

def build_report_text():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError("找不到数据文件 data/prompt_library.json")

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    prompts = data.get('prompts', [])
    total_count = len(prompts)
    
    # 1. 找出最近 24 小时内创建的 prompt (作为"今日新增")
    # 注意：这里用 tweet 的创建时间作为近似，因为采集通常是准实时的
    now = datetime.now(email.utils.parsedate_to_datetime('Mon Jan 01 00:00:00 +0000 2000').tzinfo) # 获取带时区的当前时间
    # 修正：直接用 UTC
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1.5) # 放宽到 36 小时以防时区差异

    new_prompts = []
    for p in prompts:
        dt = parse_twitter_date(p.get('created_at'))
        # 转换为 UTC naive 进行比较
        if dt.year > 2000: # 有效时间
             # 简单处理：忽略时区差异，直接比较 (tweet 时间通常是 UTC)
             ts_utc = dt.replace(tzinfo=None)
             if ts_utc > one_day_ago:
                 new_prompts.append(p)

    new_count = len(new_prompts)

    # 2. 热门榜单 (Top 5 All Time)
    # 按 likes 降序
    top_prompts = sorted(prompts, key=lambda x: x.get('likes', 0), reverse=True)[:5]

    # 3. 生成文案
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    report = f"📢 **Seedance Prompt 日报** [{today_str}]\n\n"
    
    report += f"📊 **库内统计**\n"
    report += f"- 总库存量：{total_count} 条\n"
    report += f"- 近期新增：{new_count} 条\n\n"

    report += f"🏆 **热门 Top 5 (All Time)**\n"
    
    for i, p in enumerate(top_prompts, 1):
        tags = ' '.join(p.get('tags', [])[:2]) # 只取前两个标签
        summary = p.get('summary', '无摘要')
        likes = p.get('likes', 0)
        url = p.get('tweet_url', '')
        
        if likes >= 1000:
            likes_str = f"{likes/1000:.1f}k"
        else:
            likes_str = str(likes)

        report += f"{i}. **{summary}**\n"
        report += f"   {tags} | ❤️ {likes_str} | [查看]({url})\n\n"

    report += "---\n"
    report += f"🌐 **完整库**：{GITHUB_PAGE}\n"
    report += f"💻 **GitHub**：{GITHUB_REPO}\n"
    
    return report


def generate_report(output_path=None):
    report = build_report_text()
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    print(report)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Seedance daily report')
    parser.add_argument('--output', help='Write report markdown to a file path')
    args = parser.parse_args()
    generate_report(output_path=args.output)
