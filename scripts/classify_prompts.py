#!/usr/bin/env python3
"""
使用 Gemini REST API 对 prompt 素材进行智能分类。
批量处理，每次约 25 条，减少 API 调用。
只对未分类的 prompt 进行分类（增量处理）。
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_SIZE = 25
GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'


SYSTEM_PROMPT = """你是一个AI视频内容分类专家。请为以下 Seedance AI 视频生成的 prompt 进行分析。

对每条 prompt，请返回：
1. tags: 1-2个最匹配的分类标签（从以下选择）
2. quality_score: prompt 质量评分 1-5（5=非常详细专业，1=过于简单）
3. summary: 一句话中文摘要（描述这个prompt会生成什么样的视频）

可选分类标签：
- 🎬 电影/影视
- 🎌 动漫
- 📺 广告/商业
- 🎨 艺术/创意
- 😂 搞笑/Meme
- 🌍 写实/纪实
- 🎮 游戏
- 🎵 音乐/MV
- 💡 创意/实验
- 🔥 名人/IP
- 🏷️ 其他（以上类别都不匹配时使用）

注意：如果 prompt 明确不属于以上任何一类，请使用"🏷️ 其他"。不要强行归类。

请严格按以下 JSON 数组格式返回，不要有其他内容：
[
  {"id": 1, "tags": ["🎌 动漫", "😂 搞笑/Meme"], "quality_score": 3, "summary": "海绵宝宝派大星与博尔特赛跑"},
  ...
]"""


def classify_with_gemini(prompts_batch):
    """调用 Gemini REST API 批量分类 prompt"""
    prompt_list = ""
    for i, p in enumerate(prompts_batch):
        text = p["prompt"][:200]  # 截断过长的 prompt
        prompt_list += f'{i+1}. """{text}"""\n'

    user_prompt = f"请分类以下 {len(prompts_batch)} 条 prompt：\n\n{prompt_list}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 4096,
        }
    }

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        # 提取文本
        text = data['candidates'][0]['content']['parts'][0]['text']
        text = text.strip()

        # 去掉可能的 markdown code block
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
            text = text.rsplit('```', 1)[0]
        text = text.strip()

        results = json.loads(text)
        return results

    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️ HTTP 错误: {e}")
        if resp.status_code == 429:
            print("  ⏳ 触发限流，等待 30 秒...")
            time.sleep(30)
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  ⚠️ 解析响应失败: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ API 调用失败: {e}")
        return None


def classify_prompts():
    """对 prompt_library.json 中未分类的 prompt 进行分类"""
    library_file = os.path.join(BASE_DIR, 'data', 'prompt_library.json')

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY 未设置，请在 .env 文件中配置")
        print("   跳过分类步骤，保留空标签")
        return

    if not os.path.exists(library_file):
        print("❌ prompt_library.json 不存在，请先运行 extract_prompts.py")
        return

    with open(library_file, 'r', encoding='utf-8') as f:
        library = json.load(f)

    prompts = library['prompts']

    # 找出未分类的 prompt
    unclassified = [(i, p) for i, p in enumerate(prompts) if not p.get('tags')]
    print(f"📊 总 prompt: {len(prompts)}, 待分类: {len(unclassified)}")

    if not unclassified:
        print("✅ 所有 prompt 已分类，无需处理")
        return

    # 批量分类
    total_batches = (len(unclassified) + BATCH_SIZE - 1) // BATCH_SIZE
    classified_count = 0

    for batch_idx in range(0, len(unclassified), BATCH_SIZE):
        batch = unclassified[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        print(f"\n🔄 批次 {batch_num}/{total_batches} ({len(batch)} 条)...")

        batch_prompts = [p for _, p in batch]
        results = classify_with_gemini(batch_prompts)

        if results:
            for result in results:
                idx_in_batch = result['id'] - 1
                if 0 <= idx_in_batch < len(batch):
                    original_idx = batch[idx_in_batch][0]
                    prompts[original_idx]['tags'] = result.get('tags', [])
                    prompts[original_idx]['quality_score'] = result.get('quality_score', 0)
                    prompts[original_idx]['summary'] = result.get('summary', '')
                    classified_count += 1
            print(f"  ✅ 成功分类 {len(results)} 条")
        else:
            print(f"  ❌ 批次 {batch_num} 失败，跳过")

        # 每批次后保存（防止中断丢数据）
        library['prompts'] = prompts
        with open(library_file, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)

        # 避免 API 限流
        if batch_idx + BATCH_SIZE < len(unclassified):
            time.sleep(3)

    print(f"\n✅ 分类完成: {classified_count}/{len(unclassified)} 条")
    print(f"📁 已更新: {library_file}")


if __name__ == '__main__':
    classify_prompts()
