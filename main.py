import feedparser
import os
import datetime
import pytz
from openai import OpenAI
import json

# --- 1. 核心配置 ---
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat"

# --- 2. 扩容后的数据源 (财经/技术/综合) ---
RSS_SOURCES = {
    # === 💰 硬核财经 (股市、汇率、企业) ===
    "财经-CNBC(全球)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "财经-Yahoo Finance(股市)": "https://finance.yahoo.com/news/rssindex",
    "财经-华尔街日报(中文)": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "财经-新浪财经(美股)": "https://rss.sina.com.cn/roll/finance/usstock/index.xml", # 补充中文视角
    
    # === 🤖 硬核科技 (AI、芯片、前沿) ===
    "科技-TechCrunch(创投)": "https://techcrunch.com/feed/",
    "科技-36氪(前沿)": "https://36kr.com/feed",
    "科技-MIT科技评论": "https://www.technologyreview.com/feed/",
    "科技-HackerNews(热榜)": "https://hnrss.org/newest?points=100", # 只抓高分技术贴
    
    # === 🌏 宏观与社会 ===
    "宏观-联合早报(国际)": "https://www.zaobao.com.sg/rss/realtime/world",
    "宏观-半岛电视台": "https://chinese.aljazeera.net/xml/rss/all.xml",
    
    # === 🎬 娱乐与生活 ===
    "娱乐-Yahoo Entertainment": "https://www.yahoo.com/entertainment/rss",
}

def fetch_rss_data():
    """抓取数据：大幅增加抓取量"""
    combined_content = ""
    print(">>> 正在全网搜集高价值信息...")
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"📡 正在连接: {name} ...")
            feed = feedparser.parse(url)
            
            if not feed.entries:
                continue
            
            # 提升抓取量：每个源取前 8 条，保证财经和技术有足够素材
            entries = feed.entries[:8]
            
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                title = entry.title.replace('\n', ' ')
                # 部分源可能没有 summary，做个容错
                summary = entry.get('summary', '')[:100].replace('\n', '') 
                link = entry.link
                combined_content += f"- 标题: {title}\n  简介: {summary}\n  链接: {link}\n"
                
            print(f"✅ 获取成功: {name}")
            
        except Exception as e:
            print(f"❌ 获取失败: {name} - {e}")
            
    return combined_content

def ai_summarize(content):
    """AI 分析师：生成专业研报"""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("❌ 错误：未配置 API Key")
        return None
    
    print(">>> 正在进行深度分析与撰写 (DeepSeek)...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    
    date_str = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d")

    prompt = f"""
    你是由高盛分析师与科技主编组成的“每日情报团队”。请基于以下资讯，撰写一份《{date_str} 全球深度早报》。

    【输入数据】
    {content}

    【输出强制要求】
    1. **结构与分类**：必须严格包含以下 5 个版块，每个版块挑选 5-8 条最有价值的新闻（内容要丰富）：
       ## 📈 市场与财富 (Markets & Wealth)
       *关注：美股/A股/港股核心动向、汇率波动、黄金/原油/稀有金属、知名企业财报、创始人动态。*
       
       ## 🚀 硅谷与芯片 (Tech & AI)
       *关注：AI大模型进展、英伟达/台积电等芯片巨头、硬科技突破、SaaS动态。*
       
       ## 🌏 地缘与宏观 (Geopolitics)
       *关注：大国博弈、军事冲突、央行政策、重大社会议题。*
       
       ## 💼 商业与创投 (Business & VC)
       *关注：独角兽融资、行业并购、IPO动态。*
       
       ## 🍿 生活与灵感 (Life & Inspiration)
       *关注：影视娱乐、新奇酷产品、能够让人心情愉悦的新闻。*

    2. **格式规范**：
       - **必须保留跳转链接**，格式：`* **新闻标题** - [查看原文](链接地址)`
       - 标题要“商业化”且“干练”，例如：“英伟达市值一夜蒸发400亿，黄仁勋减持套现”而不是“英伟达股价跌了”。
       - 如果原文是英文，必须翻译成流畅的中文。
    
    3. **调性**：
       - 专业、客观、具有前瞻性，剔除琐碎的无聊信息。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3500 # 增加 token 限制以容纳更多内容
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 生成失败: {e}")
        return None

def get_html_template(content, current_date, is_archive=False):
    """
    生成 HTML 页面 (包含 Tailwind CSS, 音乐播放器, 日期选择器)
    """
    # 背景音乐链接 (网易云音乐/外部 CDN 直链，选用了一首舒缓的钢琴曲)
    music_url = "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3" 
    # 或者用这个备用链接（Lofi风格）：
    # music_url = "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3"
    
    # 移除反引号
    safe_content = content.replace("`", "")

    # 如果是归档页，标题显示具体日期
    page_title = f"历史回顾: {current_date}" if is_archive else f"今日早报: {current_date}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title}</title>
        <!-- 引入 Tailwind CSS (商业感 UI 核心) -->
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <!-- 引入 Google Fonts -->
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Noto Sans SC', sans-serif; background-color: #0f172a; color: #e2e8f0; }}
            .glass-panel {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
            a {{ color: #38bdf8; transition: all 0.2s; }}
            a:hover {{ color: #7dd3fc; text-decoration: underline; }}
            h2 {{ color: #facc15; font-size: 1.5rem; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
            li {{ margin-bottom: 0.8rem; line-height: 1.7; }}
            /* 播放器样式 */
            .music-player {{ position: fixed; bottom: 20px; right: 20px; z-index: 50; }}
            .date-picker-container {{ margin-bottom: 20px; text-align: right; }}
        </style>
    </head>
    <body class="min-h-screen p-4 md:p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">

        <div class="max-w-4xl mx-auto">
            <!-- 头部区域 -->
            <header class="mb-8 text-center">
                <h1 class="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-2">
                    每日全球深度早报
                </h1>
                <p class="text-slate-400 text-sm tracking-widest uppercase">Global Intelligence Briefing | {current_date}</p>
            </header>

            <!-- 功能栏：日期选择 -->
            <div class="glass-panel rounded-xl p-4 mb-6 flex justify-between items-center">
                <div class="text-sm text-slate-300">
                    <span class="mr-2">🎵 沉浸阅读模式</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-sm text-slate-400">📅 历史回顾:</span>
                    <input type="date" id="datePicker" min="2025-11-26" class="..." ...>
                    <button onclick="gotoDate()" class="bg-blue-600 hover:bg-blue-500 text-white text-sm px-3 py-1 rounded transition">前往</button>
                    <a href="index.html" class="ml-2 text-sm text-slate-400 hover:text-white underline">回今日</a>
                </div>
            </div>

            <!-- 内容区域 -->
            <div class="glass-panel rounded-2xl p-6 md:p-10 shadow-2xl">
                <div id="content" class="prose prose-invert max-w-none">
                    <!-- AI 内容将被渲染在这里 -->
                </div>
            </div>

            <!-- 底部版权 -->
            <footer class="mt-10 text-center text-slate-500 text-xs">
                Powered by DeepSeek AI & GitHub Actions | Designed for Professionals
            </footer>
        </div>

        <!-- 隐形音频播放器 (自动播放尝试) -->
        <audio id="bgMusic" loop autoplay>
            <source src="{music_url}" type="audio/mpeg">
            您的浏览器不支持音频播放。
        </audio>
        
        <!-- 悬浮音乐控制按钮 -->
        <div class="music-player glass-panel rounded-full p-3 cursor-pointer hover:bg-slate-700 transition" onclick="toggleMusic()" title="切换音乐">
            <span id="musicIcon" class="text-2xl">🔇</span> 
            <!-- 默认静音图标，因为浏览器可能阻止自动播放，需用户点击 -->
        </div>

        <script>
            // 1. 渲染 Markdown
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);

            // 2. 日期跳转逻辑
            function gotoDate() {{
                const date = document.getElementById('datePicker').value;
                if(date) {{
                    // 跳转到 archives 目录下的对应文件
                    window.location.href = `archives/${{date}}.html`;
                }}
            }}

            // 3. 音乐播放逻辑
            const audio = document.getElementById('bgMusic');
            const icon = document.getElementById('musicIcon');
            
            // 尝试自动播放
            let playPromise = audio.play();
            if (playPromise !== undefined) {{
                playPromise.then(_ => {{
                    // 自动播放成功
                    icon.innerHTML = '🎵'; 
                }}).catch(error => {{
                    // 自动播放被阻止，显示静音图标，等待用户点击
                    icon.innerHTML = '🔇';
                    console.log("Autoplay prevented by browser, waiting for interaction.");
                }});
            }}

            function toggleMusic() {{
                if (audio.paused) {{
                    audio.play();
                    icon.innerHTML = '🎵';
                }} else {{
                    audio.pause();
                    icon.innerHTML = '🔇';
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
    # 1. 准备环境
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    # 确保归档目录存在
    os.makedirs("archives", exist_ok=True)

    try:
        # 2. 抓取与生成
        raw_data = fetch_rss_data()
        if not raw_data:
            print("⚠️ 警告：无数据")
            final_content = "今日数据源暂时不可用。"
        else:
            final_content = ai_summarize(raw_data)
            if not final_content:
                final_content = "AI 生成内容失败，请检查日志。"

        # 3. 生成今日页面 HTML
        html_today = get_html_template(final_content, today_str, is_archive=False)
        
        # 4. 生成归档页面 HTML (内容一样，但为了历史回溯，单独存一份)
        html_archive = get_html_template(final_content, today_str, is_archive=True)

        # 5. 保存文件
        # 覆盖根目录 index.html (作为今日主页)
        save_file("index.html", html_today)
        print("✅ 首页 index.html 更新完毕")
        
        # 存入 archives/YYYY-MM-DD.html (作为历史记录)
        archive_path = f"archives/{today_str}.html"
        save_file(archive_path, html_archive)
        print(f"✅ 历史归档 {archive_path} 保存完毕")

    except Exception as e:
        print(f"❌ 程序严重错误: {e}")
        exit(1)
