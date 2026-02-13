#!/usr/bin/env python3
"""
从 Apify Tweet Scraper V2 采集 Seedance 相关带视频的推文。
保存为 data/raw/YYYY-MM-DD.json
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv('APIFY_TOKEN')
ACTOR_ID = 'apidojo/tweet-scraper'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def to_actor_api_path(actor_id):
    """Apify API v2 expects actor path as `username~actor-name`."""
    if '~' in actor_id:
        return actor_id
    return actor_id.replace('/', '~')


def fetch_tweets(days_back=1, max_items=4000):
    """调用 Apify API 采集推文"""
    if not APIFY_TOKEN:
        print("❌ APIFY_TOKEN 未设置，请在 .env 文件中配置")
        sys.exit(1)

    today = datetime.utcnow()
    since_date = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')
    until_date = today.strftime('%Y-%m-%d')

    actor_input = {
        "searchTerms": [
            f"Seedance prompt since:{since_date} until:{until_date}"
        ],
        "sort": "Latest",
        "maxItems": max_items,
        "onlyVideo": True,
        "includeSearchTerms": False,
        "onlyQuote": False,
        "onlyTwitterBlue": False,
        "onlyVerifiedUsers": False,
        "onlyImage": False,
    }

    print(f"🔍 采集参数: Seedance prompt since:{since_date} until:{until_date}")
    print(f"   最大条数: {max_items}, 仅视频: True")

    # 1. 启动 Actor
    actor_path = to_actor_api_path(ACTOR_ID)
    run_url = f"https://api.apify.com/v2/acts/{actor_path}/runs?token={APIFY_TOKEN}"
    print("🚀 启动 Apify Actor...")
    resp = requests.post(run_url, json=actor_input, timeout=30)
    if not resp.ok:
        print(f"❌ 启动 Actor 失败: HTTP {resp.status_code}")
        print(resp.text[:500])
        raise RuntimeError(f"启动 Apify Actor 失败: HTTP {resp.status_code}")
    run_data = resp.json()['data']
    run_id = run_data['id']
    dataset_id = run_data['defaultDatasetId']
    print(f"   Run ID: {run_id}")
    print(f"   Dataset ID: {dataset_id}")

    # 2. 等待完成
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
    import time
    print("⏳ 等待采集完成...")
    while True:
        time.sleep(10)
        status_resp = requests.get(status_url, timeout=30)
        if not status_resp.ok:
            raise RuntimeError(f"查询 Actor 运行状态失败: HTTP {status_resp.status_code}")
        status = status_resp.json()['data']['status']
        print(f"   状态: {status}")
        if status in ('SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT'):
            break

    if status != 'SUCCEEDED':
        print(f"❌ Actor 运行失败: {status}")
        sys.exit(1)

    # 3. 下载数据
    data_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&format=json"
    print("📥 下载数据...")
    data_resp = requests.get(data_url, timeout=120)
    if not data_resp.ok:
        raise RuntimeError(f"下载 Dataset 数据失败: HTTP {data_resp.status_code}")
    raw_tweets = data_resp.json()

    print(f"   获取到 {len(raw_tweets)} 条推文")

    # 4. 精简字段
    cleaned = []
    for tweet in raw_tweets:
        cleaned.append(slim_tweet(tweet))

    # 5. 保存
    output_dir = os.path.join(BASE_DIR, 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'{since_date}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存: {output_file} ({len(cleaned)} 条)")
    return output_file


def slim_tweet(tweet):
    """精简推文字段，只保留核心数据"""
    # 处理 author 字段 - Apify 返回可能是嵌套也可能是扁平
    author = tweet.get('author', {})
    if isinstance(author, dict):
        author_info = {
            'userName': author.get('userName', ''),
            'name': author.get('name', ''),
            'followers': author.get('followers', 0),
            'isBlueVerified': author.get('isBlueVerified', False),
        }
    else:
        # 扁平格式 (CSV 导入)
        author_info = {
            'userName': tweet.get('author/userName', ''),
            'name': tweet.get('author/name', ''),
            'followers': tweet.get('author/followers', 0),
            'isBlueVerified': tweet.get('author/isBlueVerified', False),
        }

    # 处理 media 字段
    media = []
    # 尝试嵌套格式
    if 'media' in tweet and isinstance(tweet['media'], list):
        media = tweet['media']
    else:
        # 扁平格式
        for i in range(4):
            m = tweet.get(f'media/{i}', '')
            if m:
                media.append(m)

    return {
        'id': tweet.get('id', tweet.get('twitterUrl', '')),
        'url': tweet.get('url', tweet.get('twitterUrl', '')),
        'text': tweet.get('fullText', tweet.get('text', '')),
        'createdAt': tweet.get('createdAt', ''),
        'lang': tweet.get('lang', ''),
        'likeCount': int(tweet.get('likeCount', 0) or 0),
        'retweetCount': int(tweet.get('retweetCount', 0) or 0),
        'replyCount': int(tweet.get('replyCount', 0) or 0),
        'quoteCount': int(tweet.get('quoteCount', 0) or 0),
        'bookmarkCount': int(tweet.get('bookmarkCount', 0) or 0),
        'isQuote': tweet.get('isQuote', False),
        'isReply': tweet.get('isReply', False),
        'isRetweet': tweet.get('isRetweet', False),
        'author': author_info,
        'media': media,
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fetch Seedance tweets from Apify')
    parser.add_argument('--days', type=int, default=1, help='Days back to fetch')
    parser.add_argument('--max', type=int, default=4000, help='Max tweets to fetch')
    args = parser.parse_args()
    fetch_tweets(days_back=args.days, max_items=args.max)
