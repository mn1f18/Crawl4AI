from flask import Flask, request, jsonify, render_template
import openpyxl
import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

@app.route('/crawl', methods=['POST'])
def crawl():
    index = request.json.get('index', 1)  # 默认测试第一个链接
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取指定索引的链接
    link = sheet.cell(row=index+1, column=1).value  # Excel行从1开始，跳过标题行
    
    # 爬取指定链接
    result = asyncio.run(crawl_link(link))
    
    # 渲染HTML模板
    return render_template('result.html', url=result['url'], content=result['content'])

@app.route('/view_result', methods=['GET'])
def view_result():
    content_type = request.args.get('type', 'content')  # 获取查询参数，默认为'content'
    
    # 读取Excel文件
    wb = openpyxl.load_workbook('..\\testsample.xlsx')
    sheet = wb.active
    
    # 获取第一个链接
    link = sheet.cell(row=2, column=1).value  # Excel行从1开始，跳过标题行
    
    # 爬取第一个链接
    result = asyncio.run(crawl_link(link, content_type))
    
    # 渲染HTML模板
    return render_template('result.html', url=result['url'], content=result['content'], duration=result['duration'])

async def crawl_link(link, content_type='content'):
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
                'duration': crawl_duration
            }
        elif content_type == 'link':
            # 提取链接字符串
            all_links = [link['href'] for link in result.links.get('internal', []) + result.links.get('external', []) if 'href' in link]
            return {
                'url': link,
                'content': '\n'.join(all_links),
                'duration': crawl_duration
            }
        else:
            return {
                'url': link,
                'content': result.markdown,
                'duration': crawl_duration
            }

if __name__ == '__main__':
    app.run(debug=True)  
