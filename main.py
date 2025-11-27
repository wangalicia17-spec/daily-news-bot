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

# --- 2. 🎵 完整版古典/Lo-Fi 曲库 ---
MUSIC_PLAYLIST = [
    "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3", # 肖邦夜曲
    "https://cdn.pixabay.com/audio/2022/10/14/audio_9939f792cb.mp3", # 德彪西月光
    "https://cdn.pixabay.com/audio/2021/09/06/audio_9c04a27542.mp3", # 极简钢琴
    "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3", # Lo-Fi 学习
    "https://cdn.pixabay.com/audio/2021/11/01/audio_0346bf2826.mp3", # 电影感
]

# --- 3. 资讯数据源 ---
RSS_SOURCES = {
    # === 🚀 深度源 (用于最后的压轴板块) ===
    "深度-虎嗅": "https://www.huxiu.com/rss/0.xml",
    "深度-36氪": "https://36kr.com/feed",
    "深度-TheVerge": "https://www.theverge.com/rss/features/index.xml",
    "深度-HBR": "https://feeds.hbr.org/harvardbusiness",

    # === ⚡ 快讯源 (用于前5个常规板块) ===
    "快讯-华尔街日报": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "快讯-CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "快讯-MIT科技评论": "https://www.technologyreview.com/feed/",
    "快讯-联合早报": "https://www.zaobao.com.sg/rss/realtime/world",
    "快讯-TechCrunch": "https://techcrunch.com/feed/",
    "快讯-新浪美股": "https://rss.sina.com.cn/roll/finance/usstock/index.xml",
}

def fetch_rss_data():
    combined_content = ""
    print(">>> 正在全网搜集信息 (扩大抓取量)...")
    
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries: continue
            
            # 策略调整：为了保证常规板块内容够多，大幅增加快讯抓取量
            # 深度源取前 3 条，快讯源取前 10 条
            limit = 3 if "深度" in name else 10
            entries = feed.entries[:limit]
            
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                title = entry.title.replace('\n', ' ')
                summary = entry.get('summary', '')[:200].replace('\n', '') 
                link = entry.link
                published = entry.get('published', '')
                combined_content += f"- {title} | {published} | {summary} ({link})\n"
                
        except Exception as e:
            print(f"❌ 抓取失败: {name} - {e}")
            
    return combined_content

def ai_summarize(content):
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key: return None
    
    print(">>> 正在进行深度分析与撰写...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now_str = datetime.datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
    你是顶级商业媒体的主编。今天是北京时间 {now_str}。
    请基于输入数据，撰写一份《全球深度早报》。

    【输入数据】
    {content}

    【输出强制要求】
    请严格按照以下顺序和要求生成 Markdown 内容（不要遗漏任何板块）：

    ## 📈 市场与财富 (Markets & Wealth)
    *   **数量**：5-8 条。
    *   **内容**：股市、汇率、大宗商品、企业财报、创始人动态。

    ## 🚀 硅谷与芯片 (Tech & AI)
    *   **数量**：5-8 条。
    *   **内容**：AI大模型、芯片巨头、硬科技新闻。

    ## 🌏 地缘与宏观 (Geopolitics)
    *   **数量**：5-8 条。
    *   **内容**：国际局势、大国博弈、央行政策。

    ## 💼 商业与创投 (Business & VC)
    *   **数量**：5-8 条。
    *   **内容**：投融资、IPO、行业并购。

    ## 🍿 生活与灵感 (Life & Inspiration)
    *   **数量**：3-5 条。
    *   **内容**：新奇产品、影视娱乐、轻松话题。

    --- 
    (以下为压轴板块)

    ## 🧠 深度研报 (Deep Dive)
    *   **筛选标准**：从【深度】信源中，挑选 **3篇** 最具价值的长文。
    *   **位置**：必须放在文章最后。
    *   **格式**：
        ### 1. [中文标题] (原文: 媒体名)
        > **核心洞察**：用50-80字深度概括文章的核心逻辑。
        > [🔗 点击阅读深度全文](链接地址)

    【全局规则】
    1. **翻译**：所有英文标题和简介必须翻译成**专业中文**。
    2. **快讯格式**：`* **标题** - [查看原文](链接)`
    3. **去重**：深度研报中的文章，不要在快讯板块重复出现。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000 
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 生成失败: {e}")
        return None

def get_html_template(content, current_date, update_time, is_archive=False):
    playlist_js = json.dumps(MUSIC_PLAYLIST)
    safe_content = content.replace("`", "")
    page_title = f"回顾: {current_date}" if is_archive else f"早报: {current_date}"
    min_date = "2025-11-26" 

    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>{page_title}</title>
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2965/2965879.png">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Noto Sans SC', sans-serif; background-color: #0f172a; color: #e2e8f0; padding-bottom: 100px; -webkit-tap-highlight-color: transparent; }}
            .glass-panel {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
            a {{ color: #38bdf8; }}
            
            /* 深度研报特别样式 (压轴) */
            h3 {{ color: #fff; font-size: 1.1rem; font-weight: bold; margin-top: 1.5rem; margin-bottom: 0.5rem; }}
            blockquote {{ border-left: 4px solid #facc15; padding-left: 1rem; color: #94a3b8; font-style: italic; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 0 8px 8px 0; }}
            
            h2 {{ color: #facc15; font-size: 1.4rem; font-weight: bold; margin-top: 2.5rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
            li {{ margin-bottom: 1rem; line-height: 1.6; }}
            strong {{ color: #fff; font-weight: 600; }}
            
            /* 播放器样式 */
            .music-player {{ 
                position: fixed; bottom: 25px; right: 25px; z-index: 9999; 
                display: flex; gap: 12px; align-items: center; 
                background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(10px); 
                padding: 8px 12px; border-radius: 50px; 
                border: 1px solid rgba(255,255,255,0.2); 
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
            .music-btn {{ 
                width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; 
                border-radius: 50%; background: rgba(255,255,255,0.15); font-size: 20px; cursor: pointer; 
            }}
            .music-btn:active {{ background: rgba(255,255,255,0.3); transform: scale(0.95); }}
            #musicStatus {{ font-size: 12px; max-width: 150px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }}
        </style>
    </head>
    <body class="min-h-screen bg-slate-900">

        <div class="max-w-4xl mx-auto p-4 md:p-8 pt-10">
            <header class="mb-6 text-center">
                <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-1">
                    每日全球深度早报
                </h1>
                <p class="text-slate-500 text-xs uppercase tracking-widest">{current_date} | {update_time}</p>
            </header>

            <div class="glass-panel rounded-xl p-3 mb-6 flex justify-between items-center text-xs">
                <div id="topStatus" class="text-slate-400">🎵 点击右下角播放完整版音乐</div>
                <div class="flex gap-2">
                    <input type="date" id="datePicker" min="{min_date}" class="bg-slate-700 text-white rounded px-2 py-1">
                    <button onclick="gotoDate()" class="bg-blue-600 text-white px-3 py-1 rounded">回顾</button>
                    <a href="index.html" class="ml-2 text-slate-400 underline self-center">今日</a>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-5 md:p-8 shadow-2xl">
                <!-- 渲染内容 -->
                <div id="content" class="prose prose-invert max-w-none text-sm md:text-base"></div>
            </div>

            <footer class="mt-8 text-center text-slate-600 text-xs">
                Powered by DeepSeek AI
            </footer>
        </div>

        <audio id="bgMusic" preload="auto"></audio>
        
        <div class="music-player">
            <div id="musicStatus" class="text-white hidden md:block mr-2">准备就绪</div>
            <button class="music-btn" onclick="playNext()" title="下一首">⏭️</button>
            <button class="music-btn" onclick="toggleMusic()" title="播放/暂停">
                <span id="musicIcon">🔇</span>
            </button>
        </div>

        <script>
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);

            function gotoDate() {{
                const date = document.getElementById('datePicker').value;
                if(date) window.location.href = `archives/${{date}}.html`;
            }}

            const playlist = {playlist_js};
            const audio = document.getElementById('bgMusic');
            const icon = document.getElementById('musicIcon');
            const status = document.getElementById('musicStatus');
            const topStatus = document.getElementById('topStatus');
            
            let currentIndex = Math.floor(Math.random() * playlist.length);

            audio.src = playlist[currentIndex];
            // 不自动播放

            function updateUI(state) {{
                if (state === 'playing') {{
                    icon.innerHTML = '⏸️';
                    status.innerHTML = '🎵 正在播放 (完整版)';
                    topStatus.innerHTML = '🎹 沉浸阅读模式: 开启';
                }} else if (state === 'paused') {{
                    icon.innerHTML = '▶️';
                    status.innerHTML = '💤 已暂停';
                }} else if (state === 'loading') {{
                    icon.innerHTML = '⏳';
                    status.innerHTML = '📡 缓冲中...';
                }}
            }}

            function playNext() {{
                updateUI('loading');
                currentIndex = (currentIndex + 1) % playlist.length;
                audio.src = playlist[currentIndex];
                audio.play().then(() => updateUI('playing')).catch(e => updateUI('paused'));
            }}

            function toggleMusic() {{
                if (audio.paused) {{
                    updateUI('loading');
                    audio.play().then(() => updateUI('playing')).catch(e => {{
                        audio.load();
                        audio.play().then(() => updateUI('playing'));
                    }});
                }} else {{
                    audio.pause();
                    updateUI('paused');
                }}
            }}

            audio.addEventListener('ended', playNext);
        </script>
    </body>
    </html>
    """

def save_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_tz)
    today_str = now.strftime("%Y-%m-%d")
    update_time_str = now.strftime("%H:%M:%S")
    os.makedirs("archives", exist_ok=True)

    try:
        raw_data = fetch_rss_data()
        final_content = ai_summarize(raw_data) if raw_data else "暂无数据"
        if not final_content: final_content = "AI 生成失败。"

        html_today = get_html_template(final_content, today_str, update_time_str, is_archive=False)
        html_archive = get_html_template(final_content, today_str, update_time_str, is_archive=True)

        save_file("index.html", html_today)
        save_file(f"archives/{today_str}.html", html_archive)
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
