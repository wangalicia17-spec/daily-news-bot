import feedparser
import os
import datetime
import pytz
from openai import OpenAI

# --- 1. 配置区域 ---
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat"

# 【精选全方位信源】
# 这里的 Key (冒号前面的字) 会帮助 AI 识别新闻的领域
RSS_SOURCES = {
    # --- 财经 & 宏观 ---
    "财经-联合早报(商业)": "https://www.zaobao.com.sg/rss/finance",
    "财经-华尔街日报(中文)": "https://feeds.a.dj.com/rss/RSSWorldNews.xml", # 往往包含深度财经
    
    # --- 技术 (AI & 芯片) ---
    "科技-36氪(前沿)": "https://36kr.com/feed",
    "科技-MIT科技评论": "https://www.technologyreview.com/feed/",
    "科技-V2EX(热议)": "https://www.v2ex.com/index.xml",
    
    # --- 国际 & 军事 & 社会 ---
    "综合-联合早报(国际)": "https://www.zaobao.com.sg/rss/realtime/world",
    "综合-半岛电视台(中文)": "https://chinese.aljazeera.net/xml/rss/all.xml", # 军事冲突报道较多
    
    # --- 娱乐 & 生活 ---
    "娱乐-Yahoo Entertainment": "https://www.yahoo.com/entertainment/rss",
    "生活-少数派": "https://sspai.com/feed",
}

def fetch_rss_data():
    """抓取 RSS 数据"""
    combined_content = ""
    print(">>> 开始抓取全方位新闻...")
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"正在抓取: {name} ...")
            # 增加超时设置，防止卡死
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"⚠️ {name} 无内容，跳过。")
                continue
            
            # 每个源只取前 4 条，避免 Token 爆炸，但源多了总量就多了
            entries = feed.entries[:4]
            
            combined_content += f"\n【信源：{name}】\n"
            for entry in entries:
                # 稍微清洗一下标题，去掉多余的换行
                title = entry.title.replace('\n', ' ')
                link = entry.link
                combined_content += f"- {title} ({link})\n"
                
            print(f"✅ {name} 获取成功")
            
        except Exception as e:
            print(f"❌ {name} 抓取失败: {e}")
            
    return combined_content

def ai_summarize(content):
    """
    核心升级：
    让 AI 学会'分类整理'，而不仅仅是'总结'
    """
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("❌ 错误：缺少 API Key")
        return None
    
    print(">>> 正在呼叫 AI 进行深度整理...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    
    # 这里的 Prompt 是关键，教 AI 怎么做编辑
    prompt = f"""
    你是一位资深的“全媒体主编”。请阅读以下抓取到的全球资讯，为我生成一份结构清晰的《每日深度早报》。

    【输入数据】
    {content}

    【输出要求】
    1. 必须严格按照以下 5 个版块分类输出（Markdown格式）：
       ## 💰 全球财经 (重点关注市场动向)
       ## 🛡️ 军事与地缘 (重点关注冲突与政策)
       ## 🤖 技术前沿 (重点关注AI、芯片、硬科技)
       ## 🌏 社会焦点 (重点关注民生与热点)
       ## 🎬 娱乐与生活 (轻松话题)

    2. **筛选规则**：
       - 每个版块挑选 3-5 条最有价值的新闻。
       - 如果某个版块的新闻很少，可以只列 1-2 条，宁缺毋滥。
       - 如果某条新闻同时涉及科技和财经（如英伟达股价），请归类到【技术前沿】。

    3. **格式规则**：
       - 每条新闻用中文一句话概括核心事实（不要废话）。
       - 必须在每条新闻后附上原文链接。
       - 格式示例：
         * **标题/核心事件** - [链接]

    4. **语言风格**：
       - 专业、客观、干练。
       - 将英文新闻自动翻译为中文表述。
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000 # 允许生成较长的内容
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 生成失败: {e}")
        return None

def generate_html(markdown_content):
    """生成优化的 HTML"""
    if not markdown_content:
        markdown_content = "今日新闻抓取或生成失败，请检查 Actions 日志。"

    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(beijing_tz)
    date_str = now.strftime("%Y年%m月%d日")
    update_time = now.strftime("%H:%M")
    
    # 移除反引号防止 HTML 报错
    safe_content = markdown_content.replace("`", "")
    
    # 使用稍微现代一点的 CSS 样式
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>每日全览 - {date_str}</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            :root {{ --primary-color: #2563eb; --bg-color: #f8fafc; --card-bg: #ffffff; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: var(--bg-color); color: #1e293b; margin: 0; padding: 20px; line-height: 1.6; }}
            .container {{ max-width: 800px; margin: 0 auto; background: var(--card-bg); padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            
            h1 {{ text-align: center; color: #0f172a; margin-bottom: 5px; font-size: 24px; }}
            .subtitle {{ text-align: center; color: #64748b; font-size: 14px; margin-bottom: 30px; }}
            
            /* Markdown 样式优化 */
            h2 {{ color: var(--primary-color); border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; font-size: 18px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 12px; }}
            a {{ color: var(--primary-color); text-decoration: none; word-break: break-all; }}
            a:hover {{ text-decoration: underline; }}
            p {{ margin-bottom: 10px; }}
            
            @media (max-width: 600px) {{
                body {{ padding: 10px; }}
                .container {{ padding: 20px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗞️ 每日深度早报</h1>
            <div class="subtitle">{date_str} | 更新于北京时间 {update_time}</div>
            <div id="content"></div>
        </div>
        
        <script>
            document.getElementById('content').innerHTML = marked.parse(`{safe_content}`);
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    try:
        raw_data = fetch_rss_data()
        if not raw_data:
            print("⚠️ 警告：数据源为空")
            generate_html("")
        else:
            summary = ai_summarize(raw_data)
            if summary:
                generate_html(summary)
                print(">>> ✅ 网页生成完毕！")
            else:
                generate_html("AI 生成内容失败。")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        exit(0)
