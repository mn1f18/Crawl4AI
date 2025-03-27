import openpyxl
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup
import os
import json
import re
import traceback
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai import CacheMode
import requests
import pandas as pd
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

# 导入AI链接验证模块
try:
    # 尝试直接导入（当前目录下的模块）
    import ai_link_validator
    AI_LINK_VALIDATOR_AVAILABLE = True
except ImportError:
    try:
        # 尝试从上级目录导入
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import ai_link_validator
        AI_LINK_VALIDATOR_AVAILABLE = True
    except ImportError:
        print("⚠️ AI链接验证模块未找到，将使用传统方法判断链接有效性")
        AI_LINK_VALIDATOR_AVAILABLE = False

# 配置选项
SAVE_TO_EXCEL = True                # 是否保存结果到Excel
MAX_LINKS_PER_SOURCE = 100           # 每个来源最多抓取的链接数
MIN_CONTENT_LENGTH = 300            # 最小有效内容长度
MAX_RETRY_COUNT = 2                 # 链接请求失败时最大重试次数
REQUEST_TIMEOUT = 60                # 请求超时时间（秒）
SKIP_EXISTING_LINKS = True          # 是否跳过已存在的链接
LINKS_HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "link_history")  # 历史链接存储目录
USE_AI_LINK_VALIDATION = True       # 是否使用AI链接验证
USE_COLD_START = False             # 是否使用冷启动模式（跳过AI验证，直接爬取内容）

# 简化评分参数 - 仅保留基础设置
QUALITY_CONFIG = {
    "min_content_length": 300,    # 最小有效内容长度
    "min_paragraphs": 3           # 最少段落数
}

# 确保历史目录存在
if not os.path.exists(LINKS_HISTORY_DIR):
    os.makedirs(LINKS_HISTORY_DIR)

# 使用URL作为链接唯一标识
def generate_link_id(url):
    """生成链接的唯一标识，直接使用URL作为标识"""
    return url

# 添加URL规范化函数
def normalize_url(url):
    """
    规范化URL，用于链接去重
    - 转换为小写
    - 移除URL参数（如果不包含特定关键词）
    - 去除尾部斜杠
    - 移除默认端口号
    """
    if not url:
        return ""
        
    parsed = urlparse(url)
    
    # 小写处理域名
    netloc = parsed.netloc.lower()
    
    # 移除默认端口号
    if netloc.endswith(':80') and parsed.scheme == 'http':
        netloc = netloc[:-3]
    elif netloc.endswith(':443') and parsed.scheme == 'https':
        netloc = netloc[:-4]
    
    # 处理路径 - 小写并移除尾部斜杠
    path = parsed.path.lower()
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    
    # 检查是否保留查询参数 - 某些网站使用查询参数区分文章
    query = parsed.query
    
    # 保留含有这些词的查询参数，它们通常用于区分内容
    keep_query_keywords = ['id', 'article', 'news', 'post', 'story', 'p']
    
    # 如果查询参数不包含保留关键词，移除它们
    if query and not any(keyword in query.lower() for keyword in keep_query_keywords):
        query = ''
    
    # 重建URL
    normalized = urlunparse((
        parsed.scheme.lower(),
        netloc,
        path,
        parsed.params,
        query,
        '' # 移除fragment
    ))
    
    return normalized

# 检测是否为新链接并追踪链接状态
def is_new_link(url, source):
    """
    检查链接是否为新链接（未爬取过）并获取状态
    
    返回: (is_new, is_invalid, is_processed)
    is_new: 布尔值，True表示链接未爬取过
    is_invalid: 布尔值，True表示链接之前已被标记为无效
    is_processed: 布尔值，True表示链接已经被处理过（无论有效或无效）
    """
    links_history = load_links_history(source)
    
    # 直接检查URL是否存在于历史记录中
    for _, info in links_history.items():
        if info.get('url', '') == url:
            is_valid = info.get('is_valid', True)
            # 链接存在且已经抓取过内容（内容长度大于0或爬取次数大于1）
            has_content = info.get('content_length', 0) > 0 or info.get('crawl_count', 0) > 1
            return False, not is_valid, has_content
    
    # URL不存在于历史记录中，则为新链接且未处理过
    return True, False, False

# 加载历史链接数据
def load_links_history(source):
    """加载指定来源的历史链接数据"""
    history_file = os.path.join(LINKS_HISTORY_DIR, f"{source}_links.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载历史链接数据出错: {e}")
            return {}
    return {}

# 保存历史链接数据
def save_links_history(source, links_data):
    """保存指定来源的历史链接数据"""
    history_file = os.path.join(LINKS_HISTORY_DIR, f"{source}_links.json")
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(links_data, f, ensure_ascii=False, indent=2)
        print(f"成功保存历史链接数据: {history_file}")
    except Exception as e:
        print(f"保存历史链接数据出错: {e}")

# 更新链接历史记录
def update_link_history(url, title, source, content_summary="", is_valid=True, quality_score=0, content_length=0, error_message="", content_fingerprint="", ai_score=0, ai_reason="", link_type=""):
    """
    更新链接历史记录
    
    参数:
        url: 链接URL
        title: 链接标题
        source: 来源ID
        content_summary: 内容摘要
        is_valid: 是否有效的链接
        quality_score: 内容质量评分
        content_length: 内容长度
        error_message: 错误信息
        content_fingerprint: 内容指纹
        ai_score: AI验证分数
        ai_reason: AI验证理由
        link_type: 链接类型
    """
    try:
        # 加载历史记录
        links_history = load_links_history(source)
        
        # 生成链接ID
        link_id = generate_link_id(url)
        
        # 当前时间
        current_time = datetime.now().isoformat()
        
        # 检查此链接是否存在
        if link_id in links_history:
            # 更新现有记录
            links_history[link_id]['is_valid'] = is_valid
            links_history[link_id]['last_updated'] = current_time
            
            # 只有在提供了内容时才更新内容相关字段
            if content_length > 0:
                links_history[link_id]['content_length'] = content_length
                if content_summary:
                    links_history[link_id]['content_summary'] = content_summary
                if content_fingerprint:
                    links_history[link_id]['content_fingerprint'] = content_fingerprint
            
            # 更新质量评分（如果提供）
            if quality_score > 0:
                links_history[link_id]['quality_score'] = quality_score
                
            # 更新错误信息（如果有）
            if error_message:
                links_history[link_id]['error_message'] = error_message
                
            # 增加爬取次数
            links_history[link_id]['crawl_count'] = links_history[link_id].get('crawl_count', 0) + 1
                
            # 更新AI验证信息（如果提供）
            if ai_score > 0:
                links_history[link_id]['ai_score'] = ai_score
            if ai_reason:
                links_history[link_id]['ai_reason'] = ai_reason
            if link_type:
                links_history[link_id]['link_type'] = link_type
        else:
            # 创建新记录
            links_history[link_id] = {
                'url': url,
                'title': title,
                'is_valid': is_valid,
                'first_seen': current_time,
                'last_updated': current_time,
                'content_length': content_length,
                'content_summary': content_summary,
                'quality_score': quality_score,
                'error_message': error_message,
                'content_fingerprint': content_fingerprint,
                'crawl_count': 1,  # 初始爬取次数为1
                'ai_score': ai_score,
                'ai_reason': ai_reason,
                'link_type': link_type
            }
            
        # 保存更新后的历史记录
        save_links_history(source, links_history)
        
    except Exception as e:
        print(f"更新链接历史记录出错: {e}")

# 读取主界面链接
# 使用绝对路径，避免相对路径导致的问题
excel_source_file = r'C:\Python\github\Crawl4AI\testhomepage.xlsx'  # 使用原始字符串和反斜杠
# 备选相对路径，如果绝对路径不存在可以尝试
alternative_path = '../testhomepage.xlsx'

# 检查文件是否存在，如果不存在尝试备选路径
if not os.path.exists(excel_source_file):
    print(f"❌ 主路径找不到文件: {excel_source_file}，尝试备选路径...")
    if os.path.exists(alternative_path):
        excel_source_file = alternative_path
        print(f"✅ 找到备选路径文件: {excel_source_file}")
    else:
        print(f"❌ 备选路径也找不到文件: {alternative_path}")
        # 尝试列出当前目录下的Excel文件
        print("当前目录下的Excel文件:")
        for file in os.listdir('.'):
            if file.endswith('.xlsx'):
                print(f" - {file}")
        
        # 尝试列出上级目录下的Excel文件
        print("上级目录下的Excel文件:")
        for file in os.listdir('..'):
            if file.endswith('.xlsx'):
                print(f" - {file}")
else:
    print(f"✅ 找到源文件: {excel_source_file}")

wb = openpyxl.load_workbook(excel_source_file)
sheet = wb.active

# 创建结果Excel文件
def create_result_excel(filename=None):
    """创建结果Excel文件"""
    # 如果不保存到Excel，直接返回None
    if not SAVE_TO_EXCEL:
        return None
    
    # 生成文件名
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_results_{timestamp}.xlsx"
    
    # 保存全局引用
    global result_excel_file
    result_excel_file = filename
    
    # 创建工作簿和工作表
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "抓取结果"
    
    # 设置表头
    headers = [
        '索引', '来源', '链接', '标题', '发布日期', '分类', '正文字数', 
        '爬取时间(秒)', '状态', '尝试次数', 'AI验证分数', 'AI验证理由', '链接类型'
    ]
    
    # 设置列宽
    column_widths = {
        'A': 8,   # 索引
        'B': 15,  # 来源
        'C': 50,  # 链接
        'D': 50,  # 标题
        'E': 15,  # 发布日期
        'F': 15,  # 分类
        'G': 10,  # 正文字数
        'H': 15,  # 爬取时间
        'I': 20,  # 状态
        'J': 10,  # 尝试次数
        'K': 12,  # AI验证分数
        'L': 40,  # AI验证理由
        'M': 15,  # 链接类型
    }
    
    for col, width in column_widths.items():
        sheet.column_dimensions[col].width = width
    
    # 写入表头
    for idx, header in enumerate(headers, 1):
        sheet.cell(row=1, column=idx).value = header
    
    # 保存并返回
    wb.save(filename)
    print(f"已创建结果文件: {filename}")
    return filename

# 生成当前批次ID
current_batch = datetime.now().strftime("%Y%m%d_%H%M%S")
batch_id = current_batch

# 全局变量
result_excel_file = f"news_results_{batch_id}.xlsx"  # 默认Excel文件名
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_link_decisions.jsonl")  # AI验证日志文件路径
ENABLE_LOGGING = True  # 是否启用AI验证日志

# 简化评估内容质量的函数
def evaluate_content_quality(html_content, title, url=""):
    """
    简化版函数，不再评估内容质量，只返回内容摘要和指纹
    """
    if not html_content:
        return True, "", ""
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除脚本、样式和导航元素
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    
    # 获取所有文本
    text = soup.get_text(separator='\n', strip=True)
    
    # 生成内容摘要 (限制为200字)
    content_summary = text[:200] + "..." if len(text) > 200 else text
    
    # 生成内容指纹
    content_fingerprint = hashlib.md5(text[:1000].encode('utf-8')).hexdigest()
    
    # 始终返回True表示内容有效
    return True, content_summary, content_fingerprint

# 提取发布时间的函数（增强版）
def extract_publish_date(soup):
    """
    从HTML中提取发布时间，尝试多种方法
    """
    # 方法1: 查找元数据标签
    meta_properties = [
        'article:published_time', 'datePublished', 'publishedDate', 
        'pubdate', 'date', 'DC.date', 'article:modified_time', 
        'lastModified', 'og:published_time', 'og:updated_time',
        'dateCreated', 'dateModified', 'release_date'
    ]
    
    for meta in soup.find_all('meta'):
        prop = meta.get('property', '') or meta.get('name', '')
        if prop.lower() in [p.lower() for p in meta_properties]:
            content = meta.get('content')
            if content:
                return content
    
    # 方法2: 查找时间标签
    time_tags = soup.find_all('time')
    for time_tag in time_tags:
        datetime_attr = time_tag.get('datetime')
        if datetime_attr:
            return datetime_attr
        if time_tag.text.strip():
            return time_tag.text.strip()
    
    # 方法3: 根据CSS选择器查找
    date_selectors = [
        '.date', '.time', '.published', '.timestamp', '.post-date',
        '[itemprop="datePublished"]', '.article-date', '.entry-date',
        '.post-meta time', '.article-meta time', '.publish-date',
        '.updated-date', '.create-date', '.release-date', '.article-time'
    ]
    
    for selector in date_selectors:
        date_element = soup.select_one(selector)
        if date_element:
            return re.sub(r'(Published|Updated|Posted|Date):?\s*', '', date_element.get_text(strip=True))
    
    # 方法4: 在全文中查找日期模式
    # 常见日期格式：YYYY-MM-DD, DD/MM/YYYY, Month DD, YYYY等
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
        r'\d{2}\.\d{2}\.\d{4}', # DD.MM.YYYY
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}'
    ]
    
    text = soup.get_text()
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    # 没有找到日期
    return "未知"

# 提取文章标题的函数（增强版）
def extract_title(soup, url):
    """
    从HTML中提取文章标题，尝试多种方法
    """
    # 方法1: 使用<title>标签
    if soup.title:
        title = soup.title.string
        # 清理标题（移除网站名称等）
        if title:
            # 常见分隔符：|, -, –, —, :, ·, •
            for separator in [' | ', ' - ', ' – ', ' — ', ' : ', ' · ', ' • ']:
                if separator in title:
                    parts = title.split(separator)
                    # 通常第一部分是文章标题，而非网站名称
                    if len(parts[0]) > 10:  # 标题足够长
                        return parts[0].strip()
            return title.strip()
    
    # 方法2: 寻找主标题标签
    for heading in ['h1', 'h2']:
        headings = soup.find_all(heading)
        if headings:
            # 筛选最可能是标题的元素（通常位于内容区域，不在header/nav等中）
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda c: c and ('content' in c.lower() or 'article' in c.lower()))
            
            if main_content:
                content_headings = main_content.find_all(heading)
                if content_headings:
                    return content_headings[0].get_text(strip=True)
            
            # 如果不能确定内容区域，使用第一个最长的标题
            longest_heading = max(headings, key=lambda h: len(h.get_text(strip=True)))
            return longest_heading.get_text(strip=True)
    
    # 方法3: 查找元数据
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        prop = meta.get('property', '') or meta.get('name', '')
        if prop.lower() in ['og:title', 'twitter:title', 'dc.title']:
            content = meta.get('content')
            if content:
                return content
    
    # 方法4: 从URL中提取可能的标题
    path = urlparse(url).path
    segments = [seg for seg in path.split('/') if seg]
    if segments:
        # 最后一段路径可能是标题的slug
        last_segment = segments[-1]
        # 将连字符或下划线替换为空格
        title_from_url = re.sub(r'[-_]', ' ', last_segment)
        if len(title_from_url) > 5:  # 确保足够长
            return title_from_url.capitalize()
    
    # 无法确定标题
    return "未找到标题"

# 判断链接是否为有效新闻链接的函数（简化版）
def is_valid_news_link(link, base_url, a_tag=None, html_content=None):
    """
    判断链接是否为有效的新闻链接 - 简化版，主要依赖AI
    
    参数:
        link: 待验证的链接
        base_url: 基础链接
        a_tag: 可选，链接所在的a标签（BeautifulSoup对象）
        html_content: 可选，页面HTML内容
    """
    # 基础过滤 - 明显的非新闻链接
    if not link or not isinstance(link, str):
        return False
        
    if link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
        return False
        
    # 构建完整URL
    if not urlparse(link).netloc:
        full_url = urljoin(base_url, link)
        parsed_link = urlparse(full_url)
    else:
        full_url = link
        parsed_link = urlparse(full_url)
        
    # 排除非文本媒体文件
    if any(parsed_link.path.lower().endswith(ext) for ext in 
          ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.mp3', '.mp4', 
           '.css', '.js', '.ico', '.svg', '.webp', '.woff', '.ttf']):
        return False
    
    # 检查是否为同一域名（排除外部链接）
    parsed_base = urlparse(base_url)
    if parsed_link.netloc != parsed_base.netloc:
        return False

    # 优先使用AI验证模块
    if USE_AI_LINK_VALIDATION and AI_LINK_VALIDATOR_AVAILABLE:
        try:
            # 使用AI验证模块判断链接有效性
            return ai_link_validator.is_valid_news_link_with_ai(full_url, base_url, a_tag, html_content)
        except Exception as e:
            print(f"❌ AI链接验证失败，回退到基础规则: {str(e)}")
    
    # 基础过滤规则（如果AI验证不可用或失败）
    # 检查链接文本是否看起来像标题（超过20个字符且不是导航类文本）
    if a_tag and a_tag.get_text():
        link_text = a_tag.get_text().strip()
        if len(link_text) > 15:  # 放宽条件
            return True
    
    # 检查URL路径是否包含新闻相关特征
    path_lower = parsed_link.path.lower()
    return (
        '/news/' in path_lower or 
        '/article/' in path_lower or 
        '/post/' in path_lower or
        re.search(r'/20\d{2}[/-]\d{1,2}/', path_lower) is not None or
        re.search(r'/\d{4,}/', path_lower) is not None
    )

# 爬取主界面
async def fetch_news_links(main_url, source):
    """从主页获取新闻链接，按新逻辑处理链接验证和爬取"""
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True, 
        viewport_width=1366,
        viewport_height=768,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        java_script_enabled=True,
        ignore_https_errors=True
    )
    
    # 设置爬虫配置
    prune_filter = PruningContentFilter(
        threshold=0.45,
        threshold_type="dynamic",
        min_word_threshold=5
    )
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    
    crawler_config = CrawlerRunConfig(
        markdown_generator=md_generator,
        page_timeout=REQUEST_TIMEOUT * 1000,
        cache_mode=CacheMode.BYPASS
    )
    
    try:
        print(f"🔄 正在爬取主页: {main_url}")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=main_url, config=crawler_config)
            
            if not result.success:
                print(f"❌ 爬取主页失败: {main_url}, 错误: {result.error_message}")
                return []
                
            print(f"✅ 爬取主页成功: {main_url}")
            
            # 加载此源站的历史链接数据
            links_history = load_links_history(source)
            
            # 记录已知URL，用于快速查找（冷启动模式可能会跳过这些检查）
            known_urls = set()
            known_invalid_urls = set()  # 记录已知的无效URL
            already_processed_urls = set()  # 记录已处理过的URL（无论有效无效）
            content_fingerprints = set()  # 存储所有内容指纹，用于快速查找
            
            for _, info in links_history.items():
                url = info.get('url', '')
                known_urls.add(url)
                
                # 记录已知的无效URL
                if not info.get('is_valid', True):
                    known_invalid_urls.add(url)
                
                # 记录已经处理过内容的URL
                if info.get('content_length', 0) > 0 or info.get('crawl_count', 0) > 1:
                    already_processed_urls.add(url)
                
                # 记录内容指纹用于后续比较
                if info.get('content_fingerprint'):
                    content_fingerprints.add(info.get('content_fingerprint'))
                    
            print(f"⚠️ 已加载 {len(known_urls)} 个已知链接，其中 {len(known_invalid_urls)} 个无效链接")
            print(f"⚠️ 已有 {len(already_processed_urls)} 个链接已经处理过内容")
            
            try:
                # 使用BeautifulSoup处理HTML提取链接
                soup = BeautifulSoup(result.html, 'html.parser')
                all_links = soup.find_all('a', href=True)
                print(f"🔍 找到 {len(all_links)} 个原始链接")
                
                # 用于存储处理后的所有链接
                all_processed_links = []
                # 用于存储新链接（需要验证）
                new_links_to_validate = []
                
                # 添加一个集合用于链接去重
                processed_urls = set()
                skipped_duplicate_count = 0  # 记录跳过的重复链接数
                
                # 跳过的链接计数
                skipped_known_valid_count = 0  # 跳过已知有效且已处理的链接
                skipped_invalid_count = 0  # 跳过已知无效链接
                skipped_already_processed = 0  # 跳过已经处理过内容的链接（无论有效无效）
                
                for a_tag in all_links:
                    link = a_tag['href'].strip()
                    title = a_tag.get_text().strip()
                    
                    # 规范化URL - 将相对URL转为绝对URL
                    if link.startswith('/'):
                        # 相对URL，添加域名
                        parsed_url = urlparse(main_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        link = urljoin(base_url, link)
                    elif not link.startswith(('http://', 'https://')):
                        # 其他相对URL形式
                        link = urljoin(main_url, link)
                    
                    # 跳过非http(s)链接
                    if not link.startswith(('http://', 'https://')):
                        continue
                    
                    # 进一步规范化URL用于去重
                    normalized_link = normalize_url(link)
                    
                    # 链接去重检查
                    if normalized_link in processed_urls:
                        skipped_duplicate_count += 1
                        continue
                    else:
                        processed_urls.add(normalized_link)
                    
                    # 跳过已知链接（除非是冷启动模式）
                    if not USE_COLD_START:
                        # 检查是否为已知链接以及状态
                        is_new, is_invalid, is_processed = is_new_link(link, source)
                        
                        if not is_new:
                            if is_invalid:
                                # 是已知的无效链接，直接跳过
                                skipped_invalid_count += 1
                                continue
                            elif is_processed:
                                # 是已经处理过内容的有效链接，直接跳过
                                skipped_already_processed += 1
                                continue
                            else:
                                # 是已知的有效链接但未处理过内容，可能需要继续处理
                                skipped_known_valid_count += 1
                                # 根据需要决定是否跳过
                                # 由于需要爬取内容，这里不跳过，而是加入待验证列表
                    else:
                        is_new = True
                        is_invalid = False
                        is_processed = False
                    
                    # 生成链接ID
                    link_id = generate_link_id(link)
                    
                    # 收集链接信息
                    link_info = {
                        'url': link,
                        'title': title,
                        'is_new': is_new,
                        'link_id': link_id,
                        'a_tag': a_tag,
                        'crawl_time': datetime.now().isoformat(),
                        'is_valid': False,  # 默认为无效，稍后验证
                        'is_processed': is_processed,  # 记录是否已处理过内容
                    }
                    
                    all_processed_links.append(link_info)
                    
                    # 标记为需要验证的新链接或未处理过内容的链接
                    if is_new or (not is_invalid and not is_processed):
                        new_links_to_validate.append(link_info)
                
                print(f"🔄 处理后得到 {len(all_processed_links)} 个链接，其中 {len(new_links_to_validate)} 个需要验证")
                print(f"⏩ 跳过了 {skipped_duplicate_count} 个重复链接")
                print(f"⏩ 跳过了 {skipped_known_valid_count} 个已知有效链接")
                print(f"⏩ 跳过了 {skipped_invalid_count} 个已知无效链接")
                print(f"⏩ 跳过了 {skipped_already_processed} 个已处理过内容的链接")
                
                # 设置valid_links默认为空列表
                valid_links = []
                
                # 冷启动模式下，所有链接都视为有效，不进行AI验证
                if USE_COLD_START:
                    print("🚀 冷启动模式: 所有新链接都将直接爬取，不验证有效性")
                    # 设置所有链接为有效
                    for link in new_links_to_validate:
                        link['is_valid'] = True
                    valid_links = new_links_to_validate
                    
                    # 更新所有链接的历史记录（标记为有效）
                    for link in valid_links:
                        update_link_history(
                            url=link['url'],
                            title=link['title'],
                            source=source,
                            is_valid=True,
                            quality_score=50  # 冷启动模式下默认中等分数
                        )
                
                # 非冷启动模式下，使用AI验证新链接
                elif USE_AI_LINK_VALIDATION and AI_LINK_VALIDATOR_AVAILABLE and new_links_to_validate:
                    print(f"🧠 使用AI验证 {len(new_links_to_validate)} 个链接...")
                    
                    # 使用批量验证处理新链接
                    valid_links = ai_link_validator.batch_link_validation(
                        new_links_to_validate, 
                        main_url, 
                        result.html
                    )
                    
                    print(f"✅ AI验证完成，有 {len(valid_links)} 个有效链接")
                    
                    # 更新所有经过验证的链接历史记录
                    for link in new_links_to_validate:
                        # 判断此链接是否在有效链接列表中
                        is_valid = any(vl['url'] == link['url'] for vl in valid_links)
                        
                        # 重要：设置链接的is_valid属性，以便后续处理
                        link['is_valid'] = is_valid
                        
                        # 获取AI验证分数和理由（如果有）
                        ai_score = 0
                        ai_reason = ""
                        ai_link_type = ""
                        
                        # 从AI验证日志中查找此链接的记录
                        if ENABLE_LOGGING and os.path.exists(LOG_FILE):
                            try:
                                with open(LOG_FILE, "r", encoding="utf-8") as f:
                                    for line in f:
                                        try:
                                            record = json.loads(line)
                                            if record.get('url') == link['url']:
                                                ai_score = record.get('score', 0)
                                                ai_reason = record.get('reason', "")
                                                ai_link_type = "文章" if is_valid else "非文章"
                                                # 将AI信息添加到链接信息中
                                                link['ai_score'] = ai_score
                                                link['ai_reason'] = ai_reason
                                                link['link_type'] = ai_link_type
                                                break
                                        except json.JSONDecodeError:
                                            continue
                            except Exception as e:
                                print(f"读取AI验证日志时出错: {e}")
                        
                        # 更新链接历史 - 此时只更新验证状态，内容稍后爬取
                        update_link_history(
                            url=link['url'],
                            title=link['title'],
                            source=source,
                            is_valid=is_valid,
                            quality_score=ai_score,
                            content_length=0,  # 内容长度为0，表示还未爬取内容
                            error_message="" if is_valid else "AI判断为无效链接",
                            ai_score=ai_score,
                            ai_reason=ai_reason,
                            link_type=ai_link_type
                        )
                elif not USE_AI_LINK_VALIDATION:
                    print("⚠️ 未启用AI验证，所有新链接都将被视为有效")
                    valid_links = new_links_to_validate
                else:
                    print("⚠️ AI验证不可用或没有新链接需要验证")
                
                # 打印统计信息
                print(f"共找到 {len(valid_links)} 个有效链接")
                
                # 更详细的统计信息
                print(f"链接过滤详情:")
                print(f" - 原始链接总数: {len(all_links)}")
                print(f" - 跳过已知有效链接: {skipped_known_valid_count}")
                print(f" - 跳过已知无效链接: {skipped_invalid_count}")
                print(f" - 跳过已处理过内容的链接: {skipped_already_processed}")
                print(f" - 经过筛选后的链接: {len(all_processed_links)}")
                print(f" - 需要验证的链接: {len(new_links_to_validate)}")
                print(f" - 最终有效链接: {len(valid_links)}")
                
                # 添加处理状态标记和其他信息到有效链接
                for vl in valid_links:
                    # 标记为需要处理
                    vl['need_process'] = not vl.get('is_processed', False)
                
                # 优先处理新链接，最多返回MAX_LINKS_PER_SOURCE个
                return valid_links[:MAX_LINKS_PER_SOURCE]
            except Exception as e:
                print(f"处理链接时出错: {e}")
                traceback.print_exc()
                return []
    except Exception as e:
        print(f"爬取主页时出错: {e}")
        traceback.print_exc()
        return []

# 导出历史链接库到Excel（新增函数）
def export_links_history_to_excel():
    """将所有历史链接数据导出到Excel文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"links_history_{timestamp}.xlsx"
        
        # 创建工作簿和工作表
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "历史链接"
        
        # 设置表头
        headers = [
            '序号', '链接ID', '来源', 'URL', '标题', '有效性', '首次发现时间', 
            '最后更新时间', '内容长度', '质量评分', '爬取次数', 'AI验证分数', 'AI验证理由', '链接类型'
        ]
        
        # 设置列宽
        column_widths = {
            'A': 8,   # 序号
            'B': 35,  # 链接ID
            'C': 15,  # 来源
            'D': 60,  # URL
            'E': 50,  # 标题
            'F': 10,  # 有效性
            'G': 20,  # 首次发现时间
            'H': 20,  # 最后更新时间
            'I': 12,  # 内容长度
            'J': 12,  # 质量评分
            'K': 10,  # 爬取次数
            'L': 12,  # AI验证分数
            'M': 40,  # AI验证理由
            'N': 15,  # 链接类型
        }
        
        for col, width in column_widths.items():
            sheet.column_dimensions[col].width = width
        
        # 写入表头
        for idx, header in enumerate(headers, 1):
            sheet.cell(row=1, column=idx).value = header
        
        # 遍历所有历史记录文件
        row_idx = 2
        total_records = 0
        
        # 确保目录存在
        if not os.path.exists(LINKS_HISTORY_DIR):
            print(f"历史链接目录不存在: {LINKS_HISTORY_DIR}")
            return None
            
        # 获取所有历史记录文件
        history_files = [f for f in os.listdir(LINKS_HISTORY_DIR) if f.endswith('_links.json')]
        
        for history_file in history_files:
            # 提取来源ID
            source = history_file.replace('_links.json', '')
            
            # 加载数据
            file_path = os.path.join(LINKS_HISTORY_DIR, history_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    links_data = json.load(f)
                    
                # 写入数据
                for link_id, info in links_data.items():
                    # 构建数据行
                    data = [
                        row_idx - 1,  # 序号
                        link_id,      # 链接ID
                        source,       # 来源
                        info.get('url', ''),            # URL
                        info.get('title', ''),          # 标题
                        '有效' if info.get('is_valid', False) else '无效',  # 有效性
                        info.get('first_seen', ''),     # 首次发现时间
                        info.get('last_updated', ''),   # 最后更新时间
                        info.get('content_length', 0),  # 内容长度
                        info.get('quality_score', 0),   # 质量评分
                        info.get('crawl_count', 0),     # 爬取次数
                        info.get('ai_score', 0),        # AI验证分数
                        info.get('ai_reason', ''),      # AI验证理由
                        info.get('link_type', '')       # 链接类型
                    ]
                    
                    # 写入一行数据
                    for col, value in enumerate(data, 1):
                        sheet.cell(row=row_idx, column=col).value = value
                        
                    row_idx += 1
                    total_records += 1
                    
            except Exception as e:
                print(f"处理历史文件时出错 {history_file}: {e}")
                continue
        
        # 保存文件
        wb.save(filename)
        print(f"成功导出历史链接数据到 {filename}，共 {total_records} 条记录")
        return filename
        
    except Exception as e:
        print(f"导出历史链接数据时出错: {e}")
        return None

# 将抓取结果写入Excel文件
def write_result_to_excel(url, title, source_name, publish_date, content, link_duration, 
                          is_valid_content, retry_count, processed_count, ai_score=0, 
                          ai_reason="", link_type=""):
    """将抓取结果写入Excel文件"""
    if not SAVE_TO_EXCEL or not result_excel_file or not os.path.exists(result_excel_file):
        return
    
    try:
        # 加载Excel文件
        wb = openpyxl.load_workbook(result_excel_file)
        sheet = wb.active
        next_row = sheet.max_row + 1
        
        # 构建数据
        data = [
            processed_count,  # 索引
            source_name,      # 来源
            url,              # 链接
            title,            # 标题
            publish_date,     # 发布日期
            "新闻" if is_valid_content else "非新闻",  # 分类
            len(content),     # 正文字数
            f"{link_duration:.2f}",    # 爬取时间
            "成功" if is_valid_content else "失败",  # 状态
            retry_count,      # 尝试次数
            ai_score,         # AI验证分数
            ai_reason,        # AI验证理由
            link_type         # 链接类型
        ]
        
        # 写入数据
        for col, value in enumerate(data, 1):
            sheet.cell(row=next_row, column=col).value = value
            
        # 保存
        wb.save(result_excel_file)
        print(f"✅ 已将结果写入Excel: 行 {next_row}")
    except Exception as e:
        print(f"❌ 写入Excel时出错: {e}")

# 主程序
async def main():
    """主程序入口"""
    # 创建结果Excel文件
    if SAVE_TO_EXCEL:
        result_file = create_result_excel()
        print(f"📊 Excel结果将保存到: {result_excel_file}")
    
    print(f"🚀 开始新闻爬取，批次ID: {batch_id}")
    
    # 读取excel文件中的主页链接
    excel_source_file = r'C:\Python\github\Crawl4AI\testhomepage.xlsx'
    
    # 检查文件是否存在
    if not os.path.exists(excel_source_file):
        print(f"⚠️ 源文件不存在: {excel_source_file}")
        excel_source_file = "../testhomepage.xlsx"
        if not os.path.exists(excel_source_file):
            print(f"⚠️ 备用源文件也不存在: {excel_source_file}")
            return
    
    print(f"📄 找到源文件: {excel_source_file}")
    wb_source = openpyxl.load_workbook(excel_source_file)
    sheet_source = wb_source.active
    
    # 创建历史链接目录
    os.makedirs(LINKS_HISTORY_DIR, exist_ok=True)
    
    # 记录统计信息
    source_count = 0         # 处理的来源数量
    processed_count = 0      # 处理的链接数量
    success_count = 0        # 成功处理的链接数量
    error_count = 0          # 处理失败的链接数量
    skipped_count = 0        # 跳过的链接数量
    new_link_count = 0       # 新链接数量
    invalid_link_count = 0   # 无效链接数量
    
    # 遍历excel文件中的每一行
    for row in range(2, sheet_source.max_row + 1):  # 从第2行开始，跳过标题行
        try:
            remark = sheet_source.cell(row=row, column=1).value
            main_url = sheet_source.cell(row=row, column=2).value
            source_name = sheet_source.cell(row=row, column=3).value
            
            if not main_url or not source_name:
                continue
                
            source_count += 1
            
            print(f"\n🌐 处理来源 {source_count}: {remark} - {main_url} (Source ID: {source_name})")
            
            # 加载此源的历史链接
            links_history_file = os.path.join(LINKS_HISTORY_DIR, f"{source_name}_links.json")
            print(f"📋 历史链接文件: {links_history_file}")
            
            # 爬取主页中的新闻链接
            start_time = time.time()
            links = await fetch_news_links(main_url, source_name)
            end_time = time.time()
            
            print(f"⏱️ 爬取链接耗时: {end_time - start_time:.2f}秒")
            
            # 处理每个链接
            source_success_count = 0
            for link_info in links:
                processed_count += 1
                retry_count = 0
                
                # 检查链接是否已经处理过内容
                if link_info.get('is_processed', False):
                    print(f"\n⏩ 跳过已处理过内容的链接: {link_info['url']}")
                    skipped_count += 1
                    continue
                
                # 记录是否为新链接
                if link_info.get('is_new', True):
                    new_link_count += 1
                
                # 只有AI判定的有效链接才进行内容爬取
                if 'is_valid' in link_info and link_info['is_valid']:
                    while retry_count <= MAX_RETRY_COUNT:
                        try:
                            url = link_info['url']
                            title_from_link = link_info['title']
                            is_new, _, is_processed = is_new_link(url, source_name)
                            
                            # 如果已经处理过，跳过
                            if is_processed:
                                print(f"\n⏩ 跳过已处理过内容的链接: {url}")
                                break
                                
                            crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            print(f"\n🔗 正在处理链接: {url}")
                            print(f"📌 链接标题: {title_from_link}")
                            print(f"🆕 是否新链接: {'是' if is_new else '否'}")
                            
                            # 设置浏览器配置
                            browser_config = BrowserConfig(
                                browser_type="chromium",
                                headless=True, 
                                viewport_width=1366,
                                viewport_height=768,
                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                                java_script_enabled=True,
                                ignore_https_errors=True
                            )
                            
                            # 设置爬虫配置
                            prune_filter = PruningContentFilter(
                                threshold=0.45,
                                threshold_type="dynamic",
                                min_word_threshold=5
                            )
                            md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
                            
                            crawler_config = CrawlerRunConfig(
                                markdown_generator=md_generator,
                                page_timeout=REQUEST_TIMEOUT * 1000,
                                cache_mode=CacheMode.BYPASS
                            )
                            
                            # 爬取内容
                            link_start_time = time.time()
                            async with AsyncWebCrawler(config=browser_config) as crawler:
                                result = await crawler.arun(url=url, config=crawler_config)
                            link_end_time = time.time()
                            
                            # 计算爬取耗时
                            link_duration = link_end_time - link_start_time
                            
                            if result.success:
                                print(f"✅ 成功获取内容, 耗时: {link_duration:.2f}秒")
                                
                                # 使用BeautifulSoup处理HTML
                                soup = BeautifulSoup(result.html, 'html.parser')
                                title = extract_title(soup, url) or title_from_link
                                publish_date = extract_publish_date(soup) or "未找到日期"
                                content = result.markdown.fit_markdown
                                content_length = len(content)
                                
                                print(f"📝 标题: {title}")
                                print(f"📅 发布日期: {publish_date}")
                                print(f"📊 内容长度: {content_length} 字符")
                                
                                # 使用evaluate_content_quality获取摘要和指纹（不再评估内容质量）
                                _, content_summary, content_fingerprint = evaluate_content_quality(result.html, title, url)
                                
                                # AI验证通过的链接都视为有效
                                is_valid_content = True
                                
                                # 输出结果
                                print(f"✅ 成功获取内容, 耗时: {link_duration:.2f}秒")
                                print(f"💡 内容摘要:\n{content_summary}")
                                
                                # 爬取内容后，更新链接历史记录，设置内容长度以标记为已处理
                                link_info['is_processed'] = True
                                
                                # 获取AI验证信息
                                ai_score = link_info.get('ai_score', 0)
                                ai_reason = link_info.get('ai_reason', "")
                                link_type = link_info.get('link_type', "")
                                
                                # 更新链接历史
                                update_link_history(
                                    url=url,
                                    title=title,
                                    source=source_name,
                                    content_summary=content_summary,
                                    is_valid=is_valid_content,
                                    quality_score=ai_score,
                                    content_length=content_length,
                                    content_fingerprint=content_fingerprint,
                                    ai_score=ai_score,
                                    ai_reason=ai_reason,
                                    link_type=link_type
                                )
                                
                                # 写入Excel
                                if SAVE_TO_EXCEL:
                                    write_result_to_excel(
                                        url=url,
                                        title=title,
                                        source_name=source_name,
                                        publish_date=publish_date,
                                        content=content,
                                        link_duration=link_duration,
                                        is_valid_content=is_valid_content,
                                        retry_count=retry_count,
                                        processed_count=processed_count,
                                        ai_score=ai_score,
                                        ai_reason=ai_reason,
                                        link_type=link_type
                                    )
                                
                                source_success_count += 1
                                success_count += 1
                                break  # 成功，跳出重试循环
                                
                            else:
                                print(f"❌ 获取内容失败: {result.error_message}")
                                error_message = result.error_message
                                
                                # 更新链接历史记录 - 标记为获取失败
                                update_link_history(
                                    url=url,
                                    title=title_from_link,
                                    source=source_name,
                                    is_valid=False,
                                    error_message=f"爬取失败: {error_message}"
                                )
                                
                                retry_count += 1
                                if retry_count <= MAX_RETRY_COUNT:
                                    print(f"⏳ 重试 ({retry_count}/{MAX_RETRY_COUNT})...")
                                else:
                                    print(f"❌ 达到最大重试次数，放弃此链接")
                                    error_count += 1
                                    
                        except Exception as e:
                            print(f"❌ 处理链接时出错: {e}")
                            traceback.print_exc()
                            
                            # 更新链接历史记录 - 标记为处理异常
                            update_link_history(
                                url=url,
                                title=title_from_link,
                                source=source_name,
                                is_valid=False,
                                error_message=f"处理异常: {str(e)}"
                            )
                            
                            retry_count += 1
                            if retry_count <= MAX_RETRY_COUNT:
                                print(f"⏳ 重试 ({retry_count}/{MAX_RETRY_COUNT})...")
                            else:
                                print(f"❌ 达到最大重试次数，放弃此链接")
                                error_count += 1
                else:
                    # 对于无效链接，只更新历史记录，不爬取内容
                    url = link_info['url']
                    title_from_link = link_info['title']
                    invalid_link_count += 1
                    
                    # 检查是否为已知的无效链接
                    is_new, is_invalid, is_processed = is_new_link(url, source_name)
                    if not is_new and is_invalid:
                        print(f"\n🔗 跳过已知无效链接: {url}")
                        skipped_count += 1
                        continue
                        
                    print(f"\n🔗 记录新的无效链接: {url}")
                    
                    # 更新链接历史，标记为无效
                    update_link_history(
                        url=url,
                        title=title_from_link,
                        source=source_name,
                        is_valid=False,
                        quality_score=link_info.get('ai_score', 0),
                        error_message="AI判断为无效链接"
                    )
                
            # 完成当前来源的处理
            print(f"\n✅ 来源 {source_name} 处理完成，成功获取 {source_success_count} 个有效链接")
            
        except Exception as e:
            print(f"❌ 处理源 {source_name} 时出错: {e}")
            traceback.print_exc()
            continue
            
    # 详细的统计信息打印
    print(f"\n📊 爬取统计信息:")
    print(f"总共处理了 {source_count} 个来源")
    print(f"总共发现了 {processed_count + skipped_count} 个链接")
    print(f" - 其中 {new_link_count} 个是新链接")
    print(f" - 其中 {skipped_count} 个链接被跳过（已处理过或已知无效）")
    print(f"实际处理了 {processed_count} 个链接")
    print(f" - 其中 {success_count} 个有效并成功爬取")
    print(f" - 其中 {error_count} 个处理失败")
    print(f" - 其中 {invalid_link_count} 个被AI判断为无效")
    
    # 计算有效率
    if processed_count > 0:
        success_rate = (success_count / processed_count) * 100
        print(f"有效率: {success_rate:.2f}%")
    
    # 导出历史链接到Excel
    history_file = export_links_history_to_excel()
    if history_file:
        print(f"📊 历史链接已导出到: {history_file}")
    
    print(f"🏁 程序结束，批次ID: {batch_id}")

# 当直接运行此脚本时执行主函数
if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        # 调试模式：爬取单个链接
        if len(sys.argv) >= 4:
            # 格式: python test_request3.py --debug <url> <source_name>
            debug_url = sys.argv[2]
            debug_source = sys.argv[3]
            
            print(f"🔍 调试模式: 爬取单个链接")
            print(f"🔗 URL: {debug_url}")
            print(f"📌 来源: {debug_source}")
            
            # 创建结果Excel文件
            if SAVE_TO_EXCEL:
                result_file = create_result_excel()
                print(f"📊 Excel结果将保存到: {result_excel_file}")
            
            # 确保历史链接目录存在
            os.makedirs(LINKS_HISTORY_DIR, exist_ok=True)
            
            # 定义单个链接调试函数
            async def debug_single_link():
                try:
                    # 创建爬虫配置
                    browser_config = BrowserConfig(
                        browser_type="chromium",
                        viewport_width=1280, 
                        viewport_height=800,
                        java_script_enabled=True,
                        ignore_https_errors=True
                    )
                    
                    # 设置过滤器
                    prune_filter = PruningContentFilter(
                        threshold=0.45,
                        threshold_type="dynamic",
                        min_word_threshold=5
                    )
                    
                    # 设置Markdown生成器
                    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
                    
                    # 爬虫配置
                    crawler_config = CrawlerRunConfig(
                        markdown_generator=md_generator,
                        page_timeout=REQUEST_TIMEOUT * 1000,
                        cache_mode=CacheMode.BYPASS
                    )
                    
                    # 先验证链接是否为有效新闻链接
                    print(f"🧠 使用AI验证链接有效性...")
                    parsed = urlparse(debug_url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    
                    if AI_LINK_VALIDATOR_AVAILABLE:
                        # 使用AI验证
                        is_valid = ai_link_validator.is_valid_news_link_with_ai(debug_url, base_url)
                        if not is_valid:
                            print(f"❌ AI判断该链接不是有效的新闻链接，但仍将尝试爬取内容")
                    else:
                        print(f"⚠️ AI验证模块不可用，将直接爬取内容")
                    
                    print(f"🔄 开始爬取链接: {debug_url}")
                    start_time = time.time()
                    
                    # 创建爬虫实例并爬取内容
                    async with AsyncWebCrawler() as crawler:
                        result = await crawler.arun(url=debug_url, config=crawler_config)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if result.success:
                        # 解析内容
                        soup = BeautifulSoup(result.html, 'html.parser')
                        title = extract_title(soup, debug_url)
                        publish_date = extract_publish_date(soup) or "未找到日期"
                        content = result.markdown.fit_markdown if hasattr(result.markdown, 'fit_markdown') else ""
                        content_length = len(content)
                        
                        # 使用evaluate_content_quality获取摘要和指纹（不再评估内容质量）
                        _, content_summary, content_fingerprint = evaluate_content_quality(result.html, title, debug_url)
                        
                        # 获取AI验证信息
                        ai_score = 0
                        ai_reason = ""
                        link_type = ""
                        
                        # 从AI验证日志中查找此链接的记录
                        if ENABLE_LOGGING and os.path.exists(LOG_FILE):
                            try:
                                with open(LOG_FILE, "r", encoding="utf-8") as f:
                                    for line in f:
                                        try:
                                            record = json.loads(line)
                                            if record.get('url') == debug_url:
                                                ai_score = record.get('score', 0)
                                                ai_reason = record.get('reason', "")
                                                link_type = "文章" if record.get('is_valid', False) else "非文章"
                                                break
                                        except json.JSONDecodeError:
                                            continue
                            except Exception as e:
                                print(f"读取AI验证日志时出错: {e}")
                        
                        # 输出结果
                        print(f"\n✅ 爬取成功! 耗时: {duration:.2f}秒")
                        print(f"📝 标题: {title}")
                        print(f"📅 发布日期: {publish_date}")
                        print(f"📊 内容长度: {content_length}字符")
                        if ai_score > 0:
                            print(f"🧠 AI验证分数: {ai_score}/100")
                            print(f"🧠 AI验证理由: {ai_reason}")
                        print(f"💡 内容摘要:\n{content_summary}")
                        
                        # 更新历史链接
                        update_link_history(
                            url=debug_url,
                            title=title,
                            source=debug_source,
                            content_summary=content_summary,
                            is_valid=True,  # 调试模式下始终视为有效
                            quality_score=ai_score,
                            content_length=content_length,
                            content_fingerprint=content_fingerprint,
                            ai_score=ai_score,
                            ai_reason=ai_reason,
                            link_type=link_type
                        )
                        
                        # 写入Excel结果
                        if SAVE_TO_EXCEL:
                            write_result_to_excel(
                                url=debug_url,
                                title=title,
                                source_name=debug_source,
                                publish_date=publish_date,
                                content=content,
                                link_duration=duration,
                                is_valid_content=True,
                                retry_count=0,
                                processed_count=1,
                                ai_score=ai_score,
                                ai_reason=ai_reason,
                                link_type=link_type
                            )
                        
                        # 打印部分内容
                        print("\n📄 内容预览 (前500字符):")
                        print(f"{content[:500]}...")
                        print(f"\n完整内容已保存到Excel文件: {result_excel_file}")
                        
                    else:
                        print(f"\n❌ 爬取失败! 耗时: {duration:.2f}秒")
                        print(f"错误信息: {result.error_message}")
                
                except Exception as e:
                    print(f"\n⚠️ 调试模式出错: {str(e)}")
                    traceback.print_exc()
            
            # 执行单链接调试
            asyncio.run(debug_single_link())
            
        else:
            print("❌ 调试模式用法: python test_request3.py --debug <url> <source_name>")
            print("例如: python test_request3.py --debug https://example.com/news/article123 source1")
    else:
        # 正常模式：运行完整爬取流程
        asyncio.run(main()) 