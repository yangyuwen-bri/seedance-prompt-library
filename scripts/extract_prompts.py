#!/usr/bin/env python3
"""
从 all_tweets.json 中提取包含完整 prompt + 视频的推文，
生成 prompt_library.json。

筛选逻辑：
1. 推文包含明确的 prompt 文本
2. 推文附带视频内容
3. 排除 Grok 自动回复、新闻转述
4. 去重：相同 prompt 保留互动量最高的
"""

import os
import json
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def has_video(tweet):
    """检查推文是否附带视频"""
    media = tweet.get('media', [])
    if isinstance(media, list):
        for m in media:
            if isinstance(m, str):
                if 'video_thumb' in m or 'amplify_video' in m or 'ext_tw_video' in m:
                    return True
            elif isinstance(m, dict):
                if m.get('type') == 'video' or 'video' in str(m.get('url', '')):
                    return True
    # 检查正文中的链接
    text = tweet.get('text', '')
    if re.search(r'https://t\.co/\w+', text):
        return True
    return False


def get_video_thumbnail(tweet):
    """获取视频缩略图 URL"""
    media = tweet.get('media', [])
    if isinstance(media, list):
        for m in media:
            if isinstance(m, str) and ('video_thumb' in m or 'amplify_video' in m or 'ext_tw_video' in m):
                return m
            elif isinstance(m, dict):
                return m.get('thumbnail', m.get('url', ''))
    return ''


def extract_prompt_text(text):
    """从推文全文中提取 prompt 内容"""
    if not text:
        return None

    text_clean = text.replace('""', '"')

    # Pattern 1: Prompt: "xxx" 或 Prompt: xxx
    prompt_patterns = [
        r'[Pp][Rr][Oo][Mm][Pp][Tt]\s*(?:\(.*?\))?\s*[:：]\s*["""\'](.+?)["""\']',
        r'[Pp][Rr][Oo][Mm][Pp][Tt]\s*(?:\(.*?\))?\s*[:：]\s*(.+?)(?:\n\n|https://|$)',
        r'PROMPT\s*[:：]\s*["""\'](.+?)["""\']',
    ]

    for pattern in prompt_patterns:
        match = re.search(pattern, text_clean, re.DOTALL | re.IGNORECASE)
        if match:
            prompt = match.group(1).strip()
            prompt = re.sub(r'\s*#\w+.*$', '', prompt, flags=re.DOTALL)
            prompt = re.sub(r'\s*https://t\.co/\S+', '', prompt)
            prompt = prompt.strip().strip('"').strip("'").strip('\u201c').strip('\u201d')
            if len(prompt) > 10:
                return prompt

    # Pattern 2: 引号包裹的内容
    text_lower = text_clean.lower()
    if 'seedance' in text_lower:
        quoted = re.findall(r'"([^"]{15,})"', text_clean)
        if not quoted:
            quoted = re.findall(r'\u201c([^\u201d]{15,})\u201d', text_clean)
        if quoted:
            longest = max(quoted, key=len)
            if len(longest) > 15:
                return longest.strip()

    # Pattern 3: JSON 格式
    if '{' in text_clean and 'title' in text_lower:
        json_match = re.search(r'\{[\s\S]+\}', text_clean)
        if json_match and len(json_match.group(0)) > 50:
            return json_match.group(0).strip()

    # Pattern 4: 中文结构化 prompt
    if '【' in text_clean and ('prompt' in text_lower or '文生视频' in text_clean):
        struct_match = re.search(r'(【.+)', text_clean, re.DOTALL)
        if struct_match:
            prompt = struct_match.group(1).strip()
            prompt = re.sub(r'\s*#\w+.*$', '', prompt, flags=re.DOTALL)
            prompt = re.sub(r'\s*https://t\.co/\S+', '', prompt)
            if len(prompt) > 20:
                return prompt.strip()

    return None


def is_grok_response(tweet):
    """检查是否为 Grok 自动回复"""
    author = tweet.get('author', {})
    if isinstance(author, dict):
        return author.get('userName', '').lower() == 'grok'
    return False


def is_news_repost(text):
    """检查是否为新闻转述"""
    if not text:
        return False
    indicators = [
        'Chinese company ByteDance released',
        'Someone tested the new version',
        'It is impossible to distinguish',
        'just 48 hours ago',
        'Lu Huang, an AI consultant',
    ]
    return sum(1 for ind in indicators if ind.lower() in text.lower()) >= 2


def get_engagement(tweet):
    """计算互动分数"""
    likes = int(tweet.get('likeCount', 0) or 0)
    rts = int(tweet.get('retweetCount', 0) or 0)
    replies = int(tweet.get('replyCount', 0) or 0)
    quotes = int(tweet.get('quoteCount', 0) or 0)
    bookmarks = int(tweet.get('bookmarkCount', 0) or 0)
    return likes + rts * 2 + replies * 0.5 + quotes * 1.5 + bookmarks


def normalize_prompt(prompt):
    """归一化 prompt 用于去重"""
    if not prompt:
        return ''
    norm = prompt.lower().strip()
    norm = re.sub(r'[^\w\s]', '', norm)
    norm = re.sub(r'\s+', ' ', norm)
    return norm[:100]


def extract_prompts(input_file=None):
    """主流程：从全量推文中提取 prompt 素材"""
    if input_file is None:
        input_file = os.path.join(BASE_DIR, 'data', 'all_tweets.json')

    output_file = os.path.join(BASE_DIR, 'data', 'prompt_library.json')

    with open(input_file, 'r', encoding='utf-8') as f:
        tweets = json.load(f)

    print(f"📊 总推文数: {len(tweets)}")

    results = []
    stats = {'grok': 0, 'news': 0, 'no_video': 0, 'no_prompt': 0, 'blacklisted': 0}

    # 加载黑名单
    blacklist_file = os.path.join(BASE_DIR, 'data', 'blacklist.txt')
    blacklist = set()
    if os.path.exists(blacklist_file):
        with open(blacklist_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    blacklist.add(url)
        print(f"🚫 加载黑名单: {len(blacklist)} 条")

    for tweet in tweets:
        text = tweet.get('text', '')
        url = tweet.get('url', '') # Use 'url' field for consistency with blacklist

        # 过滤黑名单
        if url and url in blacklist:
            stats['blacklisted'] += 1
            continue

        if is_grok_response(tweet):
            stats['grok'] += 1
            continue

        if is_news_repost(text):
            stats['news'] += 1
            continue

        if not has_video(tweet):
            stats['no_video'] += 1
            continue

        prompt = extract_prompt_text(text)
        if not prompt:
            stats['no_prompt'] += 1
            continue

        author = tweet.get('author', {})
        engagement = get_engagement(tweet)

        results.append({
            'prompt': prompt,
            'prompt_length': len(prompt),
            'tweet_url': tweet.get('url', ''),
            'author': author.get('userName', ''),
            'author_name': author.get('name', ''),
            'author_followers': author.get('followers', 0),
            'created_at': tweet.get('createdAt', ''),
            'lang': tweet.get('lang', ''),
            'likes': int(tweet.get('likeCount', 0) or 0),
            'retweets': int(tweet.get('retweetCount', 0) or 0),
            'replies': int(tweet.get('replyCount', 0) or 0),
            'bookmarks': int(tweet.get('bookmarkCount', 0) or 0),
            'engagement_score': engagement,
            'video_thumbnail': get_video_thumbnail(tweet),
            'full_text_preview': (text[:200] + '...') if len(text) > 200 else text,
            # 以下字段由 classify_prompts.py 填充
            'tags': [],
            'quality_score': 0,
            'summary': '',
        })

    print(f"  排除 Grok 回复: {stats['grok']}")
    print(f"  排除新闻转述: {stats['news']}")
    print(f"  排除无视频: {stats['no_video']}")
    print(f"  排除无 prompt: {stats['no_prompt']}")
    print(f"  初步匹配: {len(results)}")

    # 去重
    groups = defaultdict(list)
    for r in results:
        groups[normalize_prompt(r['prompt'])].append(r)

    deduplicated = []
    dup_count = 0
    for group in groups.values():
        group.sort(key=lambda x: x['engagement_score'], reverse=True)
        deduplicated.append(group[0])
        dup_count += len(group) - 1

    deduplicated.sort(key=lambda x: x['engagement_score'], reverse=True)

    print(f"  去重移除: {dup_count}")
    print(f"  ✅ 最终素材数: {len(deduplicated)}")

    # 保存
    library = {
        'metadata': {
            'total_tweets': len(tweets),
            'prompts_extracted': len(deduplicated),
            'last_updated': '',
            'description': 'Seedance Prompt Library - AI video prompt examples with results',
        },
        'prompts': deduplicated,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, ensure_ascii=False, indent=2)

    print(f"📁 已保存: {output_file}")
    return output_file


if __name__ == '__main__':
    extract_prompts()
