#!/usr/bin/env python3
"""
一键运行完整流程：
fetch → merge → extract → classify → generate
"""

import argparse
import sys
import os

# 将 scripts 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_tweets import fetch_tweets
from merge_dedup import merge_and_dedup
from extract_prompts import extract_prompts
from classify_prompts import classify_prompts
from generate_site import generate_site


def run_pipeline(skip_fetch=False, skip_classify=False, days_back=1, max_items=4000):
    """运行完整 pipeline"""
    print("=" * 60)
    print("🚀 Seedance Prompt Library Pipeline")
    print("=" * 60)

    # Step 1: 采集
    if not skip_fetch:
        print("\n" + "=" * 60)
        print("📡 Step 1/5: 采集推文")
        print("=" * 60)
        fetch_tweets(days_back=days_back, max_items=max_items)
    else:
        print("\n⏭️  跳过采集步骤")

    # Step 2: 合并去重
    print("\n" + "=" * 60)
    print("🔄 Step 2/5: 合并去重")
    print("=" * 60)
    merge_and_dedup()

    # Step 3: 提取 prompt
    print("\n" + "=" * 60)
    print("🔍 Step 3/5: 提取 Prompt")
    print("=" * 60)
    extract_prompts()

    # Step 4: 分类
    if not skip_classify:
        print("\n" + "=" * 60)
        print("🏷️  Step 4/5: Gemini 智能分类")
        print("=" * 60)
        classify_prompts()
    else:
        print("\n⏭️  跳过分类步骤")

    # Step 5: 生成站点
    print("\n" + "=" * 60)
    print("🌐 Step 5/5: 生成展示页面")
    print("=" * 60)
    generate_site()

    print("\n" + "=" * 60)
    print("✅ Pipeline 完成！")
    print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the full Seedance prompt library pipeline')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip tweet fetching (use existing data)')
    parser.add_argument('--skip-classify', action='store_true', help='Skip Gemini classification')
    parser.add_argument('--days', type=int, default=1, help='Days back to fetch')
    parser.add_argument('--max', type=int, default=4000, help='Max tweets to fetch')
    args = parser.parse_args()

    run_pipeline(
        skip_fetch=args.skip_fetch,
        skip_classify=args.skip_classify,
        days_back=args.days,
        max_items=args.max,
    )
