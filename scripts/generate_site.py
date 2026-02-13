#!/usr/bin/env python3
"""
从 prompt_library.json 生成 README.md 和 docs/index.html。
"""

import os
import json
from datetime import datetime
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_readme(library):
    """生成 README.md"""
    prompts = library['prompts']
    meta = library['metadata']

    # 统计
    total = len(prompts)
    tags_counter = Counter()
    langs = Counter()
    for p in prompts:
        for tag in p.get('tags', []):
            tags_counter[tag] += 1
        langs[p.get('lang', 'unknown')] += 1

    top10 = prompts[:10]
    now = datetime.utcnow().strftime('%Y-%m-%d')

    readme = f"""# 🎬 Seedance Prompt Library

> A curated collection of high-quality **Seedance AI video prompts** with real video results, scraped from Twitter/X.

[![Daily Update](https://github.com/yangyuwen-bri/seedance-prompt-library/actions/workflows/daily.yml/badge.svg)](https://github.com/yangyuwen-bri/seedance-prompt-library/actions)
[![Prompts](https://img.shields.io/badge/prompts-{total}-blue)]()
[![Last Updated](https://img.shields.io/badge/updated-{now}-green)]()

### 👉 [Browse the Interactive Gallery](https://promptlib.miemieweaver.com)

## 📊 Stats

| Metric | Value |
|---|---|
| Total Prompts | **{total}** |
| Languages | {', '.join(f'{k}: {v}' for k, v in langs.most_common(5))} |
| Last Updated | {now} |

## 🏷️ Categories

| Tag | Count |
|---|---|
"""
    for tag, count in tags_counter.most_common():
        readme += f"| {tag} | {count} |\n"

    readme += f"""
## 🔥 Top 10 Prompts

"""
    for i, p in enumerate(top10, 1):
        tags_str = ' '.join(p.get('tags', []))
        summary = p.get('summary', '')
        thumb = p.get('video_thumbnail', '')
        tweet_url = p.get('tweet_url', '')
        likes = p.get('likes', 0)

        readme += f"""### #{i} ❤️ {likes} | {tags_str}
"""
        if summary:
            readme += f"> {summary}\n\n"

        readme += f"""```
{p['prompt'][:300]}
```

"""
        if thumb:
            readme += f"[![Video]({thumb})]({tweet_url})\n\n"
        else:
            readme += f"[View Tweet →]({tweet_url})\n\n"

        readme += "---\n\n"

    readme += """## 🌐 Browse All Prompts

Visit the **[Interactive Gallery](https://promptlib.miemieweaver.com)** to browse, search, and filter all prompts by category.

## 📥 Data Files

- [`data/prompt_library.json`](data/prompt_library.json) — Full prompt library (JSON)
- [`data/all_tweets.json`](data/all_tweets.json) — All collected tweets

## 🤖 How It Works

1. **Daily Collection**: Tweets mentioning "Seedance prompt" with video are collected via [Apify](https://apify.com/)
2. **Smart Extraction**: Prompts are extracted using pattern matching
3. **AI Classification**: Each prompt is categorized using Gemini AI
4. **Auto Publish**: Results are published to this repo via GitHub Actions

## 📜 License

Data sourced from public tweets. This project is for research and creative reference purposes.
"""

    output_path = os.path.join(BASE_DIR, 'README.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"📄 README.md 生成完成")


def generate_html(library):
    """生成 docs/index.html 交互式展示页"""
    prompts = library['prompts']

    # 收集所有标签
    all_tags = set()
    for p in prompts:
        for tag in p.get('tags', []):
            all_tags.add(tag)
    all_tags = sorted(all_tags)

    # 将数据内嵌到 HTML
    prompts_json = json.dumps(prompts, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Seedance Prompt Library</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: #0a0a0f;
      color: #e0e0e0;
      min-height: 100vh;
    }}

    .header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      padding: 40px 24px 30px;
      text-align: center;
      border-bottom: 1px solid rgba(255,255,255,0.05);
    }}

    .header h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      background: linear-gradient(135deg, #e94560, #ff6b6b, #ffd93d);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }}

    .header p {{
      color: #8899aa;
      font-size: 0.95rem;
    }}

    .stats {{
      display: flex;
      justify-content: center;
      gap: 30px;
      margin-top: 20px;
      flex-wrap: wrap;
    }}

    .stat {{
      text-align: center;
    }}

    .stat-num {{
      font-size: 1.8rem;
      font-weight: 700;
      color: #e94560;
    }}

    .stat-label {{
      font-size: 0.75rem;
      color: #667788;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}

    .controls {{
      padding: 20px 24px;
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
    }}

    .search-box {{
      flex: 1;
      min-width: 250px;
      padding: 10px 16px;
      background: #1a1a2e;
      border: 1px solid #2a2a4e;
      border-radius: 10px;
      color: #e0e0e0;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.3s;
    }}

    .search-box:focus {{
      border-color: #e94560;
    }}

    .search-box::placeholder {{ color: #556; }}

    .tags-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .tag-btn {{
      padding: 6px 14px;
      border: 1px solid #2a2a4e;
      border-radius: 20px;
      background: transparent;
      color: #8899aa;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }}

    .tag-btn:hover {{
      border-color: #e94560;
      color: #e94560;
    }}

    .tag-btn.active {{
      background: #e94560;
      border-color: #e94560;
      color: #fff;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
      padding: 20px 24px;
      max-width: 1400px;
      margin: 0 auto;
    }}

    .card {{
      background: #12121f;
      border: 1px solid #1e1e35;
      border-radius: 14px;
      overflow: hidden;
      transition: transform 0.2s, box-shadow 0.2s;
    }}

    .card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 30px rgba(233,69,96,0.15);
      border-color: #e94560;
    }}

    .card-thumb {{
      width: 100%;
      height: 200px;
      object-fit: cover;
      display: block;
      background: #0d0d1a;
      cursor: pointer;
    }}

    .card-thumb-placeholder {{
      width: 100%;
      height: 200px;
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #445;
      font-size: 2rem;
    }}

    .card-body {{
      padding: 16px;
    }}

    .card-tags {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}

    .card-tag {{
      font-size: 0.7rem;
      padding: 3px 8px;
      background: rgba(233,69,96,0.15);
      color: #e94560;
      border-radius: 10px;
    }}

    .card-prompt {{
      font-size: 0.88rem;
      line-height: 1.5;
      color: #ccc;
      margin-bottom: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
      cursor: pointer;
    }}

    .card-prompt.expanded {{
      -webkit-line-clamp: unset;
      line-clamp: unset;
    }}

    .card-summary {{
      font-size: 0.78rem;
      color: #889;
      margin-bottom: 10px;
      font-style: italic;
    }}

    .card-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.75rem;
      color: #667;
    }}

    .card-engagement {{
      display: flex;
      gap: 10px;
    }}

    .card-engagement span {{ display: flex; align-items: center; gap: 3px; }}

    .card-author {{
      color: #e94560;
      text-decoration: none;
    }}

    .card-author:hover {{ text-decoration: underline; }}

    .card-quality {{
      display: flex;
      gap: 2px;
    }}

    .star {{ color: #ffd93d; font-size: 0.7rem; }}
    .star.empty {{ color: #333; }}

    .no-results {{
      text-align: center;
      padding: 60px 24px;
      color: #556;
      font-size: 1.1rem;
    }}

    .tweet-link {{
      display: inline-block;
      margin-top: 8px;
      padding: 5px 12px;
      background: rgba(29,161,242,0.15);
      color: #1da1f2;
      border-radius: 6px;
      text-decoration: none;
      font-size: 0.75rem;
      transition: background 0.2s;
    }}

    .tweet-link:hover {{
      background: rgba(29,161,242,0.3);
    }}

    .counter {{
      padding: 0 24px;
      max-width: 1400px;
      margin: 0 auto;
      font-size: 0.85rem;
      color: #556;
    }}

    @media (max-width: 768px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .header h1 {{ font-size: 1.6rem; }}
      .stats {{ gap: 15px; }}
    }}
    /* Modal Styles */
    .modal {{
      display: none; 
      position: fixed; 
      z-index: 1000; 
      left: 0;
      top: 0;
      width: 100%; 
      height: 100%; 
      overflow: auto; 
      background-color: rgba(0,0,0,0.85); 
      backdrop-filter: blur(5px);
      align-items: center;
      justify-content: center;
    }}
    .modal-content {{
      background-color: #1a1a2e;
      margin: auto;
      padding: 0;
      border: 1px solid #888;
      width: 90%;
      max-width: 600px;
      border-radius: 12px;
      position: relative;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      animation: zoomIn 0.3s;
    }}
    @keyframes zoomIn {{
      from {{transform: scale(0.9); opacity: 0;}} 
      to {{transform: scale(1); opacity: 1;}}
    }}
    .close {{
      color: #aaa;
      float: right;
      font-size: 28px;
      font-weight: bold;
      position: absolute;
      right: 15px;
      top: 5px;
      z-index: 10;
      cursor: pointer;
    }}
    .close:hover,
    .close:focus {{
      color: #e94560;
      text-decoration: none;
      cursor: pointer;
    }}
    #tweet-container {{
      min-height: 300px;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }}
  </style>
  <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</head>
<body>

<div class="header">
  <h1>🎬 Seedance Prompt Library</h1>
  <p style="margin-bottom: 6px;">Created by <a href="https://github.com/yangyuwen-bri" style="color: #e94560; text-decoration: none; font-weight: 600;">@yangyuwen-bri</a></p>
  <p>AI video prompt examples with real results, from Twitter/X</p>
  <div class="stats">
    <div class="stat">
      <div class="stat-num" id="totalCount">{len(prompts)}</div>
      <div class="stat-label">Prompts</div>
    </div>
    <div class="stat">
      <div class="stat-num" id="tagCount">{len(all_tags)}</div>
      <div class="stat-label">Categories</div>
    </div>
    <div class="stat">
      <div class="stat-num" id="topLikes">-</div>
      <div class="stat-label">Top Likes</div>
    </div>
  </div>
</div>

<div class="controls">
  <input type="text" class="search-box" id="searchInput" placeholder="🔍 Search prompts...">
  <div class="tags-bar" id="tagsBar">
    <button class="tag-btn active" data-tag="all">All</button>
  </div>
</div>

<div class="counter" id="counter"></div>
<div class="grid" id="grid"></div>
<div class="no-results" id="noResults" style="display:none">No prompts found matching your criteria</div>

<!-- The Modal -->
<div id="videoModal" class="modal" onclick="closeVideo(event)">
  <div class="modal-content">
    <span class="close" onclick="closeVideo(event)">&times;</span>
    <div id="tweet-container"></div>
  </div>
</div>

  <script type="application/json" id="data-prompts">
    {prompts_json}
  </script>
  <script>
    const PROMPTS = JSON.parse(document.getElementById('data-prompts').textContent);

    // Init
    const allTags = new Set();
PROMPTS.forEach(p => (p.tags || []).forEach(t => allTags.add(t)));

// Top likes
const maxLikes = Math.max(...PROMPTS.map(p => p.likes || 0));
document.getElementById('topLikes').textContent = maxLikes >= 1000 ? (maxLikes/1000).toFixed(1)+'K' : maxLikes;

// Build tag buttons
const tagsBar = document.getElementById('tagsBar');
[...allTags].sort().forEach(tag => {{
  const btn = document.createElement('button');
  btn.className = 'tag-btn';
  btn.dataset.tag = tag;
  btn.textContent = tag;
  tagsBar.appendChild(btn);
}});

let activeTag = 'all';
let searchQuery = '';

tagsBar.addEventListener('click', e => {{
  if (!e.target.classList.contains('tag-btn')) return;
  tagsBar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
  activeTag = e.target.dataset.tag;
  render();
}});

document.getElementById('searchInput').addEventListener('input', e => {{
  searchQuery = e.target.value.toLowerCase();
  render();
}});

function render() {{
  const grid = document.getElementById('grid');
  const noResults = document.getElementById('noResults');
  const counter = document.getElementById('counter');

  const filtered = PROMPTS.filter(p => {{
    const matchTag = activeTag === 'all' || (p.tags || []).includes(activeTag);
    const matchSearch = !searchQuery ||
      p.prompt.toLowerCase().includes(searchQuery) ||
      (p.summary || '').toLowerCase().includes(searchQuery) ||
      (p.author || '').toLowerCase().includes(searchQuery);
    return matchTag && matchSearch;
  }});

  counter.textContent = `Showing ${{filtered.length}} / ${{PROMPTS.length}} prompts`;

  if (filtered.length === 0) {{
    grid.innerHTML = '';
    noResults.style.display = 'block';
    return;
  }}
  noResults.style.display = 'none';

  grid.innerHTML = filtered.map(p => {{
    const tags = (p.tags || []).map(t => `<span class="card-tag">${{t}}</span>`).join('');
    const stars = Array.from({{length: 5}}, (_, i) =>
      `<span class="star ${{i < (p.quality_score||0) ? '' : 'empty'}}">★</span>`
    ).join('');

    // Extract Tweet ID
    const tweetId = p.tweet_url ? p.tweet_url.split('/').pop() : '';

    const thumb = p.video_thumbnail
      ? `<div class="card-image" onclick="openVideo('${{tweetId}}')" style="cursor: pointer; position: relative;">
           <img class="card-thumb" src="${{p.video_thumbnail}}" alt="Video thumbnail" loading="lazy" onerror="this.src='https://abs.twimg.com/sticky/default_profile_images/default_profile_400x400.png'">
           <div class="play-icon" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 3rem; color: rgba(255,255,255,0.8); text-shadow: 0 2px 4px rgba(0,0,0,0.5);">▶</div>
         </div>`
      : '<div class="card-thumb-placeholder">🎬</div>';

    const summary = p.summary ? `<div class="card-summary">${{p.summary}}</div>` : '';

    return `<div class="card">
      ${{thumb}}
      <div class="card-body">
        <div class="card-tags">${{tags}} <span class="card-quality">${{stars}}</span></div>
        <div class="card-prompt" onclick="this.classList.toggle('expanded')">${{escapeHtml(p.prompt)}}</div>
        ${{summary}}
        <div class="card-meta">
          <div class="card-engagement">
            <span>❤️ ${{formatNum(p.likes)}}</span>
            <span>🔄 ${{formatNum(p.retweets)}}</span>
            <span>📖 ${{formatNum(p.bookmarks)}}</span>
          </div>
          <a class="card-author" href="https://x.com/${{p.author}}" target="_blank">@${{p.author}}</a>
        </div>
        <a class="tweet-link" href="${{p.tweet_url}}" target="_blank">View on X →</a>
      </div>
    </div>`;
  }}).join('');
}}

function escapeHtml(s) {{
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}}

function formatNum(n) {{
  n = n || 0;
  return n >= 1000 ? (n/1000).toFixed(1)+'K' : n;
}}

// Modal Logic
const modal = document.getElementById("videoModal");
const container = document.getElementById("tweet-container");

function openVideo(tweetId) {{
  if (!tweetId) return;
  modal.style.display = "flex";
  container.innerHTML = ""; // Clear previous
  
  // Create Tweet Embed
  twttr.widgets.createTweet(
    tweetId,
    container,
    {{
      theme: 'dark',
      align: 'center',
      conversation: 'none'
    }}
  ).then( function( el ) {{
    console.log('Tweet displayed.');
  }});
}}

function closeVideo(event) {{
  if (event.target == modal || event.target.className == 'close' || (event.key === 'Escape')) {{
    modal.style.display = "none";
    container.innerHTML = "";
  }}
}}

// Close on Escape key
document.onkeydown = function(evt) {{
    evt = evt || window.event;
    if (evt.keyCode == 27) {{
        modal.style.display = "none";
        container.innerHTML = "";
    }}
}};

render();
</script>
</body>
</html>"""

    output_path = os.path.join(BASE_DIR, 'docs', 'index.html')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"🌐 docs/index.html 生成完成")


def generate_site():
    """生成 README 和 HTML 展示页"""
    library_file = os.path.join(BASE_DIR, 'data', 'prompt_library.json')

    if not os.path.exists(library_file):
        print("❌ prompt_library.json 不存在")
        return

    with open(library_file, 'r', encoding='utf-8') as f:
        library = json.load(f)

    print(f"📦 加载 {len(library['prompts'])} 条 prompt")

    # 加载黑名单
    blacklist_file = os.path.join(BASE_DIR, 'data', 'blacklist.txt')
    blacklist = set()
    if os.path.exists(blacklist_file):
        with open(blacklist_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    blacklist.add(url)

    # 过滤黑名单
    original_count = len(library['prompts'])
    library['prompts'] = [p for p in library['prompts'] if p.get('tweet_url') not in blacklist]
    filtered_count = len(library['prompts'])
    
    if original_count != filtered_count:
        print(f"🚫 过滤黑名单: {original_count - filtered_count} 条 (剩余 {filtered_count} 条)")

    generate_readme(library)
    generate_html(library)

    print("✅ 站点生成完成")


if __name__ == '__main__':
    generate_site()
