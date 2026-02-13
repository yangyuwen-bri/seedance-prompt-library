#!/usr/bin/env python3
"""
合并 data/raw/*.json 中的所有推文数据，按 tweet ID 去重。
输出 data/all_tweets.json
"""

import os
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def merge_and_dedup():
    """合并所有原始数据文件并去重"""
    raw_dir = os.path.join(BASE_DIR, 'data', 'raw')
    output_file = os.path.join(BASE_DIR, 'data', 'all_tweets.json')

    # 读取现有合并数据
    existing = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            for tweet in json.load(f):
                tid = tweet.get('id') or tweet.get('url', '')
                if tid:
                    existing[tid] = tweet

    print(f"📂 现有数据: {len(existing)} 条")

    # 读取所有 raw 文件
    raw_files = sorted(glob.glob(os.path.join(raw_dir, '*.json')))
    new_count = 0

    for fpath in raw_files:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            tweets = json.load(f)

        file_new = 0
        for tweet in tweets:
            tid = tweet.get('id') or tweet.get('url', '')
            if tid and tid not in existing:
                existing[tid] = tweet
                file_new += 1
                new_count += 1

        print(f"  📄 {fname}: {len(tweets)} 条, 新增 {file_new}")

    # 按时间排序（最新在前）
    all_tweets = sorted(
        existing.values(),
        key=lambda x: x.get('createdAt', ''),
        reverse=True
    )

    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_tweets, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 合并完成: {output_file}")
    print(f"   总计: {len(all_tweets)} 条, 本次新增: {new_count}")
    return output_file


if __name__ == '__main__':
    merge_and_dedup()
