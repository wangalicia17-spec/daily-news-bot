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

# --- 2. 🎵 极速加载曲库 (精选体积小、加载快的源) ---
MUSIC_PLAYLIST = [
    "https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3", # 治愈钢琴 (主打)
    "https://cdn.pixabay.com/audio/2021/11/24/audio_82339594f7.mp3", # 冥想
    "https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d0.mp3", # 空灵
    "https://cdn.pixabay.com/audio/2021/09/06/audio_9c04a27542.mp3", # 情感
]

# --- 3. 数据源配置 ---
RSS_SOURCES = {
    # === 💰 财经 ===
    "财经-CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "财经-华尔街日报": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "财经-新浪美股": "https://rss.sina.com.cn/roll/finance/usstock/index.xml",
    # === 🤖 科技 ===
    "科技-36氪": "https://36kr.com/feed",
    "科技-MIT评论": "https://www.technologyreview.com/feed/",
    "科技-TechCrunch": "https://techcrunch.com/feed/",
    # === 🌏 综合 ===
    "宏观-联合早报": "https://www.zaobao.com.sg/rss/realtime/world",
    "娱乐-Yahoo": "https://www.yahoo.com/entertainment/rss",
}

def fetch_rss_data():
    combined_content = ""
    print(">>> 正在搜集信息...")
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries: continue
            entries = feed.entries[:6]
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                title = entry.title.replace('\n', ' ')
                summary = entry.get('summary', '')[:100].replace('\n', '') 
                link = entry.link
                combined_content += f"- {title} | {summary} ({link})\n"
        except Exception: pass
    return combined_content

def ai_summarize(content):
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key: return None
    
    print(">>> AI 分析中...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now_str = datetime.datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
    今天是北京时间 {now_str}。请撰写一份《全球早报》。
    【输入数据】{content}
    【要求】
    1. 包含5个版块：
       ## 📈 市场与财富
       ## 🚀 硅谷与芯片
       ## 🌏 地缘与宏观
       ## 💼 商业与创投
       ## 🍿 生活与灵感
    2. **所有英文标题和简介必须翻译成中文**。
    3. 格式：`* **标题** - [链接](URL)`。
    4. 每个版块 4-6 条，去重，风格干练。
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
        print(f"AI Error: {e}")
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
            h2 {{ color: #facc15; font-size: 1.4rem; font-weight: bold; margin-top: 2rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
            li {{ margin-bottom: 1rem; line-height: 1.6; }}
            strong {{ color: #fff; font-weight: 600; }}
            
            /* --- 播放器暴力修复样式 --- */
            .music-player {{ 
                position: fixed; bottom: 25px; right: 25px; z-index: 9999; 
                display: flex; gap: 12px; align-items: center; 
                background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(10px); 
                padding: 8px 12px; border-radius: 50px; 
                border: 1px solid rgba(255,255,255,0.2); 
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
            .music-btn {{ 
                width: 44px; height: 44px; 
                display: flex; align-items: center; justify-content: center; 
                border-radius: 50%; background: rgba(255,255,255,0.15); 
                font-size: 20px; cursor: pointer; touch-action: manipulation;
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
                <div id="topStatus" class="text-slate-400">🎵 点击右下角播放音乐</div>
                <div class="flex gap-2">
                    <input type="date" id="datePicker" min="{min_date}" class="bg-slate-700 text-white rounded px-2 py-1">
                    <button onclick="gotoDate()" class="bg-blue-600 text-white px-3 py-1 rounded">回顾</button>
                    <a href="index.html" class="ml-2 text-slate-400 underline self-center">今日</a>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-5 md:p-8 shadow-2xl">
                <div id="content" class="prose prose-invert max-w-none text-sm md:text-base"></div>
            </div>

            <footer class="mt-8 text-center text-slate-600 text-xs">
                Powered by DeepSeek AI
            </footer>
        </div>

        <!-- 音频标签：增加 preload 属性 -->
        <audio id="bgMusic" preload="auto"></audio>
        
        <!-- 悬浮播放器 -->
        <div class="music-player">
            <div id="musicStatus" class="text-white hidden md:block mr-2">准备就绪</div>
            <button class="music-btn" onclick="playNext()" title="下一首">⏭️</button>
            <button class="music-btn" onclick="toggleMusic()" title="播放/暂停">
                <span id="musicIcon">🔇</span> <!-- 默认显示静音 -->
            </button>
        </div>

        <script>
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);

            function gotoDate() {{
                const date = document.getElementById('datePicker').value;
                if(date) window.location.href = `archives/${{date}}.html`;
            }}

            // --- 修复版音乐逻辑 ---
            const playlist = {playlist_js};
            const audio = document.getElementById('bgMusic');
            const icon = document.getElementById('musicIcon');
            const status = document.getElementById('musicStatus');
            const topStatus = document.getElementById('topStatus');
            
            let currentIndex = Math.floor(Math.random() * playlist.length);
            let isPlaying = false;

            // 初始化加载，但不自动播放（iOS不允许）
            audio.src = playlist[currentIndex];
            audio.load(); // 预加载

            function updateUI(state) {{
                if (state === 'playing') {{
                    icon.innerHTML = '⏸️'; // 显示暂停键
                    status.innerHTML = '🎵 正在播放...';
                    topStatus.innerHTML = '🎹 沉浸模式: 开启';
                    isPlaying = true;
                }} else if (state === 'paused') {{
                    icon.innerHTML = '▶️'; // 显示播放键
                    status.innerHTML = '💤 已暂停';
                    topStatus.innerHTML = '💤 点击右下角继续';
                    isPlaying = false;
                }} else if (state === 'loading') {{
                    icon.innerHTML = '⏳';
                    status.innerHTML = '📡 缓冲中...';
                }}
            }}

            function playNext() {{
                updateUI('loading');
                currentIndex = (currentIndex + 1) % playlist.length;
                audio.src = playlist[currentIndex];
                audio.load();
                
                // 必须在 promise 中处理
                audio.play().then(() => {{
                    updateUI('playing');
                }}).catch(e => {{
                    console.log("Play error:", e);
                    updateUI('paused');
                }});
            }}

            function toggleMusic() {{
                if (audio.paused) {{
                    updateUI('loading');
                    // 尝试播放
                    let playPromise = audio.play();
                    if (playPromise !== undefined) {{
                        playPromise.then(() => {{
                            updateUI('playing');
                        }}).catch(error => {{
                            console.log("Play failed, retrying load");
                            // 暴力重载
                            audio.load();
                            audio.play().then(() => updateUI('playing'));
                        }});
                    }}
                }} else {{
                    audio.pause();
                    updateUI('paused');
                }}
            }}

            audio.addEventListener('ended', playNext);
            audio.addEventListener('error', function(e) {{
                console.log("Error loading audio", e);
                status.innerHTML = "❌ 加载失败，切歌中...";
                setTimeout(playNext, 1000); // 1秒后自动切歌
            }});

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
