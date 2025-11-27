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

# --- 2. 🎵 升级版：高雅轻音乐曲库 (钢琴/大提琴/氛围) ---
# 这些链接精选自 Pixabay，风格舒缓，适合阅读
MUSIC_PLAYLIST = [
    "https://cdn.pixabay.com/audio/2022/03/10/audio_c8c8a73467.mp3", # 治愈钢琴 Main
    "https://cdn.pixabay.com/audio/2021/11/24/audio_82339594f7.mp3", # 冥想氛围
    "https://cdn.pixabay.com/audio/2022/02/07/audio_6583995eb2.mp3", # 柔美钢琴
    "https://cdn.pixabay.com/audio/2021/09/06/audio_9c04a27542.mp3", # 情感钢琴
    "https://cdn.pixabay.com/audio/2022/01/18/audio_d0a13f69d0.mp3", # 空灵
    "https://cdn.pixabay.com/audio/2020/05/27/audio_823a31e847.mp3", # 晨间
    "https://cdn.pixabay.com/audio/2021/11/25/audio_9158359265.mp3", # 电影感
    "https://cdn.pixabay.com/audio/2021/11/01/audio_0346bf2826.mp3", # 专注
]

# --- 3. 扩容后的数据源 (保留之前的配置) ---
RSS_SOURCES = {
    # === 💰 硬核财经 ===
    "财经-CNBC(全球)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
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
            
            # 这里的数量决定了 AI 能看到多少素材，建议保持在 5-8 条
            entries = feed.entries[:6]
            
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                title = entry.title.replace('\n', ' ')
                summary = entry.get('summary', '')[:150].replace('\n', '') 
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
    
    # 获取精确时间，放入 Prompt 确保每次生成内容不同，强制触发 Git 提交
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now_str = datetime.datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    prompt = f"""
    你是由高盛分析师与科技主编组成的“每日情报团队”。今天是北京时间 {now_str}。
    请基于以下资讯，撰写一份《全球深度早报》。

    【输入数据】
    {content}

    【输出强制要求】
    1. **结构与分类**：必须严格包含以下 5 个版块，每个版块挑选 4-6 条最有价值的新闻：
       ## 📈 市场与财富 (Markets & Wealth)
       ## 🚀 硅谷与芯片 (Tech & AI)
       ## 🌏 地缘与宏观 (Geopolitics)
       ## 💼 商业与创投 (Business & VC)
       ## 🍿 生活与灵感 (Life & Inspiration)

    2. **翻译与重写（重要）**：
       - **所有英文新闻的标题和简介，必须翻译成流畅、专业的中文**。不要出现英文标题。
       - 标题风格要“商业化”且“干练”，例如：“英伟达市值一夜蒸发400亿”而不是“Nvidia股价下跌”。

    3. **格式规范**：
       - 格式：`* **中文新闻标题** - [查看原文](链接地址)`
       - 必须保留原文跳转链接。
    
    4. **内容去重**：如果多条新闻讲同一件事，请合并为一条。
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

def get_html_template(content, current_date, update_time, is_archive=False):
    playlist_js = json.dumps(MUSIC_PLAYLIST)
    safe_content = content.replace("`", "")
    page_title = f"历史回顾: {current_date}" if is_archive else f"今日早报: {current_date}"
    
    # 日期选择器逻辑
    min_date = "2025-11-26" 

    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>{page_title}</title>
        <!-- iOS 优化 -->
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2965/2965879.png">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Noto Sans SC', sans-serif; background-color: #0f172a; color: #e2e8f0; padding-bottom: 80px; }}
            .glass-panel {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
            a {{ color: #38bdf8; transition: all 0.2s; }}
            a:hover {{ color: #7dd3fc; text-decoration: underline; }}
            h2 {{ color: #facc15; font-size: 1.4rem; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
            li {{ margin-bottom: 1rem; line-height: 1.7; }}
            strong {{ color: #e2e8f0; font-weight: 600; }}
            
            /* 播放器样式优化 */
            .music-player {{ position: fixed; bottom: 20px; right: 20px; z-index: 50; display: flex; gap: 8px; align-items: center; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(5px); padding: 5px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.1); }}
            .music-btn {{ width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(255,255,255,0.1); transition: all 0.2s; cursor: pointer; }}
            .music-btn:active {{ transform: scale(0.95); background: rgba(255,255,255,0.2); }}
        </style>
    </head>
    <body class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">

        <div class="max-w-4xl mx-auto p-4 md:p-8">
            <header class="mb-8 text-center pt-8">
                <h1 class="text-3xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-2">
                    每日全球深度早报
                </h1>
                <p class="text-slate-400 text-xs md:text-sm tracking-widest uppercase">
                    {current_date} | 生成时间: {update_time}
                </p>
            </header>

            <div class="glass-panel rounded-xl p-4 mb-6 flex justify-between items-center flex-wrap gap-4">
                <div class="text-xs md:text-sm text-slate-300 flex items-center overflow-hidden whitespace-nowrap">
                    <span id="musicStatus" class="animate-pulse">🎵 正在连接高雅音乐库...</span>
                </div>
                <div class="flex items-center gap-2 ml-auto">
                    <input type="date" id="datePicker" min="{min_date}" class="bg-slate-700 text-white border border-slate-600 rounded px-2 py-1 text-xs focus:outline-none">
                    <button onclick="gotoDate()" class="bg-blue-600 text-white text-xs px-3 py-1 rounded">回顾</button>
                    <a href="index.html" class="ml-2 text-xs text-slate-400 underline">今日</a>
                </div>
            </div>

            <div class="glass-panel rounded-2xl p-5 md:p-10 shadow-2xl">
                <div id="content" class="prose prose-invert max-w-none text-sm md:text-base"></div>
            </div>

            <footer class="mt-10 text-center text-slate-600 text-xs pb-10">
                Powered by DeepSeek AI & GitHub Actions
            </footer>
        </div>

        <audio id="bgMusic">您的浏览器不支持音频播放。</audio>
        
        <div class="music-player shadow-xl">
            <button class="music-btn text-lg" onclick="playNext()" title="切歌">⏭️</button>
            <button class="music-btn text-xl" onclick="toggleMusic()" title="播放/暂停">
                <span id="musicIcon">🔇</span>
            </button>
        </div>

        <script>
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);

            function gotoDate() {{
                const date = document.getElementById('datePicker').value;
                if(date) window.location.href = `archives/${{date}}.html`;
            }}

            // --- 音乐控制逻辑 ---
            const playlist = {playlist_js};
            const audio = document.getElementById('bgMusic');
            const icon = document.getElementById('musicIcon');
            const status = document.getElementById('musicStatus');
            let currentIndex = Math.floor(Math.random() * playlist.length);

            function loadTrack(index) {{
                if (index >= playlist.length) index = 0;
                currentIndex = index;
                audio.src = playlist[currentIndex];
                audio.volume = 0.6; // 默认音量 60% 防止吓人
            }}

            function playMusic() {{
                audio.play().then(() => {{
                    icon.innerHTML = '⏸️'; // 显示暂停图标
                    status.innerHTML = `🎹 正在播放: 精选辑 No.${{currentIndex + 1}}`;
                    status.classList.remove('animate-pulse');
                }}).catch(e => {{
                    console.log("Auto-play blocked");
                    icon.innerHTML = '🔇';
                    status.innerHTML = '💤 点击右下角播放音乐';
                }});
            }}

            function playNext() {{
                loadTrack(currentIndex + 1);
                playMusic();
            }}

            function toggleMusic() {{
                if (audio.paused) {{
                    // 如果还没源，先加载
                    if (!audio.src) loadTrack(currentIndex);
                    playMusic();
                }} else {{
                    audio.pause();
                    icon.innerHTML = '▶️';
                    status.innerHTML = '💤 音乐已暂停';
                }}
            }}

            // 初始化
            loadTrack(currentIndex);
            
            // 自动连播
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
    # 生成精确时间，用于显示在页面上验证是否更新
    update_time_str = now.strftime("%H:%M:%S")
    
    os.makedirs("archives", exist_ok=True)

    try:
        raw_data = fetch_rss_data()
        final_content = ai_summarize(raw_data) if raw_data else "暂无数据"
        if not final_content: final_content = "AI 生成失败，请查看日志。"

        # 传递 update_time_str 到模板
        html_today = get_html_template(final_content, today_str, update_time_str, is_archive=False)
        html_archive = get_html_template(final_content, today_str, update_time_str, is_archive=True)

        save_file("index.html", html_today)
        save_file(f"archives/{today_str}.html", html_archive)
        print(f"✅ 更新完成。生成时间: {update_time_str}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        exit(1)
