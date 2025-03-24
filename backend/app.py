from flask import Flask, request, jsonify, render_template
import openpyxl
import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from datetime import datetime
import requests
from config import DS_API_KEY

app = Flask(__name__)

@app.route('/crawl', methods=['POST'])
def crawl():
    index = request.json.get('index', 1)  # 默认测试第一个链接
    use_ds = request.json.get('use_ds', False)  # 是否使用 ds 接口
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取指定索引的链接
    link = sheet.cell(row=index+1, column=1).value  # Excel行从1开始，跳过标题行
    
    # 爬取指定链接
    result = asyncio.run(crawl_link(link, 'content', index))
    
    # 处理 ds 接口
    ds_result = 'DS interface not used'
    if use_ds:
        ds_result = process_with_ds(result['content'])
        result['ds_result'] = ds_result
    
    # 返回结果，但不渲染HTML
    return jsonify({
        'url': result['url'],
        'content': result['content'],
        'duration': result['duration'],
        'index': result['index']
    })

@app.route('/view_result', methods=['GET'])
def view_result():
    content_type = request.args.get('type', 'content')  # 获取查询参数，默认为'content'
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取前两个链接
    links = []
    for i in range(1, 3):  # 获取第1和第2个链接
        link = sheet.cell(row=i+1, column=1).value  # Excel行从1开始，跳过标题行
        if link:
            links.append(link)
    
    # 并行爬取所有链接
    results = asyncio.run(crawl_links(links, content_type))
    
    # 渲染HTML模板
    return render_template('results.html', results=results, type=content_type)

@app.route('/view_truecontent', methods=['GET'])
def view_truecontent():
    # 获取正文内容
    content_type = 'truecontent'
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取前两个链接
    links = []
    for i in range(1, 3):  # 获取第1和第2个链接
        link = sheet.cell(row=i+1, column=1).value  # Excel行从1开始，跳过标题行
        if link:
            links.append(link)
    
    # 并行爬取所有链接
    results = asyncio.run(crawl_links(links, content_type))
    
    # 计算字符数量并处理DS接口
    use_ds = request.args.get('use_ds', 'false').lower() == 'true'
    
    for result in results:
        # 计算字符数
        result['token_count'] = len(result['content'])
        
        # 处理DS接口
        result['ds_result'] = 'DS interface not used'
        if use_ds:
            result['ds_result'] = process_with_ds(result['content'])
    
    # 渲染HTML模板
    return render_template('truecontent_multi.html', results=results, prompt='default_prompt')

@app.route('/ds_check', methods=['POST'])
def ds_check():
    # 从请求中获取正文内容
    content = request.json.get('content', '')
    
    # 使用 ds 接口进行处理
    # 这里假设有一个函数 `process_with_ds` 来处理内容
    result = process_with_ds(content)
    
    # 返回处理结果
    return jsonify({'result': result})

# 假设的处理函数
# 这里你需要实现与 ds 接口的实际交互逻辑
def process_with_ds(content):
    # 使用 DS_API_KEY 进行处理
    url = "https://api.ds.example.com/analyze"  # 假设的 ds 接口 URL
    headers = {
        "Authorization": f"Bearer {DS_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "content": content
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('analysis', 'No analysis found')
    else:
        return f"Error: {response.status_code}"

async def crawl_links(links, content_type='content'):
    async with AsyncWebCrawler() as crawler:
        tasks = [crawl_link(link, content_type, index) for index, link in enumerate(links, start=1)]
        return await asyncio.gather(*tasks)

async def crawl_link(link, content_type='content', index=None):
    async with AsyncWebCrawler() as crawler:
        start_time = datetime.now()
        result = await crawler.arun(url=link)
        end_time = datetime.now()
        crawl_duration = (end_time - start_time).total_seconds()
        if content_type == 'title':
            # 从 HTML 中提取标题
            soup = BeautifulSoup(result.html, 'html.parser')
            title = soup.title.string if soup.title else 'No title found'
            return {
                'url': link,
                'content': title,
                'duration': crawl_duration,
                'index': index
            }
        elif content_type == 'link':
            # 提取链接字符串
            all_links = [link['href'] for link in result.links.get('internal', []) + result.links.get('external', []) if 'href' in link]
            return {
                'url': link,
                'content': '\n'.join(all_links),
                'duration': crawl_duration,
                'index': index
            }
        elif content_type == 'truecontent':
            # 使用多种选择器尝试提取正文内容
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # 多个可能的内容选择器，按优先级排序
            content_selectors = [
                'div.content', 'div.article-content', 'article', 
                'div.post-content', 'div.entry-content', 'main',
                '.article-body', '.news-content', '#content',
                '.story-body', '.entry', '.post'
            ]
            
            content = None
            # 尝试每个选择器
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    content = content_element.get_text(strip=True)
                    break
            
            # 如果所有选择器都失败，尝试使用 Crawl4AI 的 markdown 提取
            if not content or content == '':
                # 如果结构化提取失败，使用 Crawl4AI 的 markdown
                if hasattr(result, 'markdown') and result.markdown:
                    content = result.markdown
                else:
                    # 最后的后备方案：获取所有文本
                    content = soup.get_text(strip=True)
                    
            # 如果内容仍然为空，返回错误消息
            if not content or content == '':
                content = 'No content could be extracted from this page'
                
            return {
                'url': link,
                'content': content,
                'duration': crawl_duration,
                'index': index
            }
        else:
            return {
                'url': link,
                'content': result.markdown,
                'duration': crawl_duration,
                'index': index
            }

@app.route('/view_all_results', methods=['GET'])
def view_all_results():
    content_type = request.args.get('type', 'content')  # 获取查询参数，默认为'content'
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取第1和第2个链接
    links = []
    for i in range(1, 3):  # 仅获取第1和第2个链接
        link = sheet.cell(row=i+1, column=1).value  # Excel行从1开始，跳过标题行
        if link:
            links.append(link)
    
    # 并行爬取所有链接
    results = asyncio.run(crawl_links(links, content_type))
    
    # 渲染HTML模板
    return render_template('all_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)  
