import feedparser
import os
import datetime
import pytz
from openai import OpenAI
import json
import random

# --- 1. 核心配置 ---
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat"

# --- 2. 音乐曲库 (精选适合阅读的轻音乐/白噪音) ---
# 这些链接来自 Pixabay 等免费无版权源，支持外链播放
MUSIC_PLAYLIST = [
    "https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3", # 舒缓钢琴
    "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3", # Lo-Fi 学习
    "https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d0.mp3", # 氛围电子
    "https://cdn.pixabay.com/audio/2021/11/24/audio_82339594f7.mp3", # 冥想
    "https://cdn.pixabay.com/audio/2022/03/23/audio_07963dc558.mp3", # 柔和吉他
]

# --- 3. 扩容后的数据源 ---
RSS_SOURCES = {
    # === 💰 硬核财经 ===
    "财经-CNBC(全球)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "财经-Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "财经-华尔街日报(中文)": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "财经-新浪财经(美股)": "https://rss.sina.com.cn/roll/finance/usstock/index.xml",
    
    # === 🤖 硬核科技 ===
    "科技-TechCrunch": "https://techcrunch.com/feed/",
    "科技-36氪": "https://36kr.com/feed",
    "科技-MIT科技评论": "https://www.technologyreview.com/feed/",
    "科技-HackerNews": "https://hnrss.org/newest?points=100",
    
    # === 🌏 宏观与社会 ===
    "宏观-联合早报": "https://www.zaobao.com.sg/rss/realtime/world",
    "宏观-半岛电视台": "https://chinese.aljazeera.net/xml/rss/all.xml",
    
    # === 🎬 娱乐与生活 ===
    "娱乐-Yahoo Ent": "https://www.yahoo.com/entertainment/rss",
}

def fetch_rss_data():
    combined_content = ""
    print(">>> 正在全网搜集高价值信息...")
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"📡 正在连接: {name} ...")
            feed = feedparser.parse(url)
            if not feed.entries: continue
            
            entries = feed.entries[:8]
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                title = entry.title.replace('\n', ' ')
                summary = entry.get('summary', '')[:100].replace('\n', '') 
                link = entry.link
                combined_content += f"- 标题: {title}\n  简介: {summary}\n  链接: {link}\n"
            print(f"✅ 获取成功: {name}")
        except Exception as e:
            print(f"❌ 获取失败: {name} - {e}")
            
    return combined_content

def ai_summarize(content):
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key: return None
    
    print(">>> 正在进行深度分析与撰写...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    date_str = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    prompt = f"""
    你是由高盛分析师与科技主编组成的“每日情报团队”。请基于以下资讯，撰写一份《{date_str} 全球深度早报》。

    【输入数据】
    {content}

    【输出强制要求】
    1. **结构与分类**：必须严格包含以下 5 个版块，每个版块挑选 5-8 条最有价值的新闻：
       ## 📈 市场与财富 (Markets & Wealth)
       ## 🚀 硅谷与芯片 (Tech & AI)
       ## 🌏 地缘与宏观 (Geopolitics)
       ## 💼 商业与创投 (Business & VC)
       ## 🍿 生活与灵感 (Life & Inspiration)

    2. **格式规范**：
       - **必须保留跳转链接**，格式：`* **新闻标题** - [查看原文](链接地址)`
       - 标题要“商业化”且“干练”。
       - 英文新闻必须翻译成中文。
    
    3. **调性**：专业、客观、具有前瞻性。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 生成失败: {e}")
        return None

def get_html_template(content, current_date, is_archive=False):
    # 将 Python 列表转换为 JavaScript 数组字符串
    playlist_js = json.dumps(MUSIC_PLAYLIST)
    
    safe_content = content.replace("`", "")
    page_title = f"历史回顾: {current_date}" if is_archive else f"今日早报: {current_date}"
    
    # 设置日期选择器的最小值（防止选到 404 的日期）
    # 这里写死为今天之前的某一天作为起点，或者你可以每次运行都更新这个值
    min_date = "2025-11-26" 

    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Noto Sans SC', sans-serif; background-color: #0f172a; color: #e2e8f0; }}
            .glass-panel {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
            a {{ color: #38bdf8; transition: all 0.2s; }}
            a:hover {{ color: #7dd3fc; text-decoration: underline; }}
            h2 {{ color: #facc15; font-size: 1.5rem; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
            li {{ margin-bottom: 0.8rem; line-height: 1.7; }}
            .music-player {{ position: fixed; bottom: 20px; right: 20px; z-index: 50; display: flex; gap: 10px; align-items: center; }}
        </style>
    </head>
    <body class="min-h-screen p-4 md:p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">

        <div class="max-w-4xl mx-auto">
            <header class="mb-8 text-center">
                <h1 class="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-2">
                    每日全球深度早报
                </h1>
                <p class="text-slate-400 text-sm tracking-widest uppercase">Global Intelligence Briefing | {current_date}</p>
            </header>

            <div class="glass-panel rounded-xl p-4 mb-6 flex justify-between items-center flex-wrap gap-4">
                <div class="text-sm text-slate-300 flex items-center">
                    <span id="musicStatus">🎵 正在加载播放列表...</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-sm text-slate-400">📅 历史回顾:</span>
                    <input type="date" id="datePicker" min="{min_date}" class="bg-slate-700 text-white border border-slate-600 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500">
                    <button onclick="gotoDate()" class="bg-blue-600 hover:bg-blue-500 text-white text-sm px-3 py-1 rounded transition">前往</button>
                    <a href="index.html" class="ml-2 text-sm text-slate-400 hover:text-white underline">回今日</a>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-6 md:p-10 shadow-2xl">
                <div id="content" class="prose prose-invert max-w-none"></div>
            </div>

            <footer class="mt-10 text-center text-slate-500 text-xs">
                Powered by DeepSeek AI & GitHub Actions
            </footer>
        </div>

        <audio id="bgMusic">
            您的浏览器不支持音频播放。
        </audio>
        
        <!-- 悬浮播放控件 -->
        <div class="music-player">
            <!-- 上一首 -->
            <button class="glass-panel rounded-full p-3 hover:bg-slate-700 transition" onclick="playNext()" title="切歌">
                ⏭️
            </button>
            <!-- 播放/暂停 -->
            <button class="glass-panel rounded-full p-3 hover:bg-slate-700 transition" onclick="toggleMusic()" title="播放/暂停">
                <span id="musicIcon">🔇</span>
            </button>
        </div>

        <script>
            // 1. 内容渲染
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);

            // 2. 日期跳转
            function gotoDate() {{
                const date = document.getElementById('datePicker').value;
                if(date) window.location.href = `archives/${{date}}.html`;
            }}

            // 3. 智能曲库系统
            const playlist = {playlist_js}; // 注入 Python 定义的曲库
            const audio = document.getElementById('bgMusic');
            const icon = document.getElementById('musicIcon');
            const status = document.getElementById('musicStatus');
            let currentTrackIndex = Math.floor(Math.random() * playlist.length); // 随机开始

            function loadAndPlay(index) {{
                if (index >= playlist.length) index = 0;
                currentTrackIndex = index;
                audio.src = playlist[currentTrackIndex];
                
                // 尝试播放
                audio.play().then(() => {{
                    icon.innerHTML = '🎵';
                    status.innerHTML = `🎵 正在播放: 第 ${{currentTrackIndex + 1}} 首 (共 ${{playlist.length}} 首)`;
                }}).catch(e => {{
                    icon.innerHTML = '🔇';
                    status.innerHTML = '💤 音乐已就绪 (点击右下角播放)';
                }});
            }}

            // 初始化加载一首
            loadAndPlay(currentTrackIndex);

            // 自动连播功能：一首结束后，放下一首
            audio.addEventListener('ended', () => {{
                playNext();
            }});

            // 切歌
            function playNext() {{
                let nextIndex = currentTrackIndex + 1;
                loadAndPlay(nextIndex);
            }}

            // 开关控制
            function toggleMusic() {{
                if (audio.paused) {{
                    audio.play();
                    icon.innerHTML = '🎵';
                    status.innerHTML = `🎵 正在播放: 第 ${{currentTrackIndex + 1}} 首`;
                }} else {{
                    audio.pause();
                    icon.innerHTML = '🔇';
                    status.innerHTML = '💤 音乐已暂停';
                }}
            }}
        </script>
    </body>
    </html>
    """

def save_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    beijing_tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.datetime.now(beijing_tz).strftime("%Y-%m-%d")
    os.makedirs("archives", exist_ok=True)

    try:
        raw_data = fetch_rss_data()
        final_content = ai_summarize(raw_data) if raw_data else "暂无数据"
        if not final_content: final_content = "AI 生成失败"

        html_today = get_html_template(final_content, today_str, is_archive=False)
        html_archive = get_html_template(final_content, today_str, is_archive=True)

        save_file("index.html", html_today)
        save_file(f"archives/{today_str}.html", html_archive)
        print("✅ 网页更新完成 (包含随机曲库)")

    except Exception as e:
        print(f"❌ 错误: {e}")
        exit(1)
