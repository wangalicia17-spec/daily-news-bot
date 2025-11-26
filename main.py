import feedparser
import os
import datetime
import pytz
from openai import OpenAI

# --- 配置区域 ---
# 使用 DeepSeek 的 API (兼容 OpenAI 格式)
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat"

# 精选的新闻源 (由简入繁，这里选用了较稳定的源)
RSS_SOURCES = {
    "科技前沿 (36Kr)": "https://36kr.com/feed",
    "全球资讯 (联合早报)": "https://www.zaobao.com.sg/rss/realtime/world",
    "中国财经 (财新网)": "http://k.caixin.com/web/rss/news_cbd.xml",
    "知乎每日精选": "https://www.zhihu.com/rss",
}

def fetch_rss_data():
    """抓取 RSS 数据"""
    combined_content = ""
    print("正在抓取新闻...")
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            # 每个源只取前 5 条，避免内容过多
            entries = feed.entries[:5]
            combined_content += f"\n【来源：{name}】\n"
            for entry in entries:
                title = entry.title
                link = entry.link
                combined_content += f"- {title} ({link})\n"
        except Exception as e:
            print(f"抓取 {name} 失败: {e}")
    return combined_content

def ai_summarize(content):
    """调用 AI 进行总结"""
    print("正在呼叫 AI 进行分析...")
    client = OpenAI(api_key=os.environ.get("LLM_API_KEY"), base_url=API_BASE)
    
    prompt = f"""
    你是一个专业的新闻编辑。请根据以下抓取到的全球新闻列表，生成一份“每日早报”。
    
    要求：
    1. 语气专业、轻松，适合早上阅读。
    2. 将新闻分为三个板块：【🌏 全球风云】、【📈 财经科技】、【💬 社交热点】。
    3. 从提供的内容中挑选最重要的 8-10 条新闻。
    4. 每条新闻用一句话总结核心，并附上原文链接（Markdown格式）。
    5. 如果内容中有英文，请翻译成中文。
    
    待处理内容：
    {content}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_html(markdown_content):
    """生成漂亮的 HTML 页面"""
    beijing_tz = pytz.timezone('Asia/Shanghai')
    date_str = datetime.datetime.now(beijing_tz).strftime("%Y年%m月%d日")
    
    # 简单的 HTML 模板
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>每日早报 - {date_str}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f9; color: #333; }}
            .container {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}
            h2 {{ color: #3498db; margin-top: 25px; }}
            li {{ margin-bottom: 10px; line-height: 1.6; }}
            a {{ color: #e74c3c; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .footer {{ text-align: center; margin-top: 40px; font-size: 12px; color: #888; }}
        </style>
        <!-- 引入 Markdown 渲染库 -->
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>☕ 每日精选早报 <br><small style="font-size: 16px; color: #666;">{date_str}</small></h1>
            <div id="content"></div>
        </div>
        <div class="footer">Powered by GitHub Actions & AI</div>

        <script>
            // 将 AI 生成的 Markdown 渲染为 HTML
            const markdownText = `{markdown_content.replace('`', '\`')}`; 
            document.getElementById('content').innerHTML = marked.parse(markdownText);
        </script>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    raw_data = fetch_rss_data()
    if raw_data:
        summary = ai_summarize(raw_data)
        generate_html(summary)
        print("网页生成完毕！")
    else:
        print("未抓取到数据。")
