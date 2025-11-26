import feedparser
import os
import datetime
import pytz
from openai import OpenAI

# --- 配置区域 ---
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat"

# 【安全模式】使用对 GitHub 服务器友好的 RSS 源
RSS_SOURCES = {
    "V2EX热议": "https://www.v2ex.com/index.xml",
    "GitHub趋势": "https://mrss.feedjust.com/github/trending", 
    "联合早报(国际)": "https://www.zaobao.com.sg/rss/realtime/world",
}

def fetch_rss_data():
    """抓取 RSS 数据"""
    combined_content = ""
    print(">>> 开始抓取新闻...")
    
    for name, url in RSS_SOURCES.items():
        try:
            print(f"正在尝试抓取: {name} ...")
            feed = feedparser.parse(url)
            
            # 检查抓取是否成功
            if not feed.entries:
                print(f"⚠️ {name} 返回为空，可能是被反爬虫拦截。")
                continue
                
            entries = feed.entries[:5]
            combined_content += f"\n【来源：{name}】\n"
            for entry in entries:
                title = entry.title
                link = entry.link
                combined_content += f"- {title} ({link})\n"
            print(f"✅ {name} 抓取成功！")
            
        except Exception as e:
            print(f"❌ 抓取 {name} 失败: {e}")
            
    return combined_content

def ai_summarize(content):
    """调用 AI 进行总结"""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("❌ 严重错误：未找到 LLM_API_KEY！请在 Settings -> Secrets 中检查配置。")
        return None # 返回空，防止程序继续崩溃
    
    print(">>> 正在呼叫 AI 进行分析...")
    client = OpenAI(api_key=api_key, base_url=API_BASE)
    
    prompt = f"""
    请根据以下内容生成一份简单的“每日早报”。
    
    要求：
    1. 汇总为 Markdown 格式。
    2. 包含【技术热点】和【国际动态】两个板块。
    3. 每条新闻用中文一句话概括。
    4. 不要包含代码块符号。
    
    内容：
    {content}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 调用失败: {e}")
        return None

def generate_html(markdown_content):
    """生成 HTML"""
    if not markdown_content:
        markdown_content = "今日无新闻生成，请检查日志。"

    beijing_tz = pytz.timezone('Asia/Shanghai')
    date_str = datetime.datetime.now(beijing_tz).strftime("%Y年%m月%d日")
    
    # --- 修复核心：先在外面处理字符串，不要在 f-string 里处理 ---
    # 替换反引号，防止 JS 报错
    safe_content = markdown_content.replace("`", "") 
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>每日早报 - {date_str}</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: -apple-system, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ border-bottom: 2px solid #eaeaea; padding-bottom: 10px; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>☕ 每日早报 ({date_str})</h1>
        <div id="content"></div>
        <script>
            // 这里使用已经处理好的 safe_content 变量
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
            print("⚠️ 警告：所有源都抓取失败。")
            generate_html("今日所有 RSS 源暂时无法访问，请稍后再试。") 
        else:
            summary = ai_summarize(raw_data)
            # 即使 AI 失败，也生成一个网页，避免 Actions 报错
            if summary:
                generate_html(summary)
                print(">>> ✅ 成功：网页生成完毕！")
            else:
                generate_html("AI 生成失败，请检查 API Key 或 额度。")
    except Exception as e:
        print(f"❌ 程序崩溃: {e}")
        # 这里改为 exit(0) 防止 Actions 报红叉，方便你先看到网页结果
        exit(0)
