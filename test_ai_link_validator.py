import sys
import os
import json
import asyncio
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

# 导入AI链接验证模块
try:
    import ai_link_validator
except ImportError:
    print("错误: AI链接验证模块未找到，请确保ai_link_validator.py文件在当前目录")
    sys.exit(1)

def print_colored(text, color):
    """打印带颜色的文本"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def fetch_html(url):
    """获取URL的HTML内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print_colored(f"获取URL内容失败: {e}", "red")
        return None

def test_single_link(url, base_url=None):
    """测试单个链接"""
    if not base_url:
        # 如果未提供基础URL，使用输入URL的域名部分
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    print_colored(f"测试链接: {url}", "blue")
    print(f"基础URL: {base_url}")
    
    # 获取HTML内容
    html_content = fetch_html(url)
    if not html_content:
        print_colored("无法获取HTML内容，仅使用URL进行测试", "yellow")
    
    # 创建简单的A标签对象供测试
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        a_tags = soup.find_all('a', href=True)
        # 尝试找到一个与测试URL匹配的A标签
        a_tag = None
        for tag in a_tags:
            if tag['href'] == url or url.endswith(tag['href']):
                a_tag = tag
                break
    else:
        a_tag = None
    
    # 开始测试
    print_colored("开始AI链接验证...", "cyan")
    result = ai_link_validator.is_valid_news_link_with_ai(url, base_url, a_tag, html_content)
    
    if result:
        print_colored("✅ AI判断结果: 有效的新闻链接", "green")
    else:
        print_colored("❌ AI判断结果: 无效的新闻链接", "red")
    
    # 查看判断日志
    if ai_link_validator.ENABLE_LOGGING and os.path.exists(ai_link_validator.LOG_FILE):
        try:
            with open(ai_link_validator.LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    # 获取最后一条记录
                    last_record = json.loads(lines[-1])
                    if last_record.get('url') == url:
                        print("\n判断详情:")
                        print(f"  分数: {last_record.get('score', 'N/A')}/100")
                        print(f"  是否有效: {last_record.get('is_valid', False)}")
                        print(f"  理由: {last_record.get('reason', 'N/A')}")
                    else:
                        print("\n没有找到当前URL的判断记录")
        except Exception as e:
            print(f"读取日志文件出错: {e}")
    
    return result

def test_batch_links(urls, base_url=None):
    """测试批量链接"""
    links_info = []
    
    for url in urls:
        if not base_url:
            # 如果未提供基础URL，使用输入URL的域名部分
            parsed = urlparse(url)
            link_base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            link_base_url = base_url
            
        links_info.append({
            'url': url,
            'a_tag': None,
            'title': f"测试链接 {url}"
        })
    
    print_colored(f"批量测试 {len(links_info)} 个链接...", "blue")
    
    # 批量验证
    valid_links = ai_link_validator.batch_link_validation(links_info, base_url or "", None)
    
    print_colored(f"批量测试结果: {len(valid_links)}/{len(links_info)} 个有效链接", "green")
    
    for link in valid_links:
        print(f"✅ {link['url']}")
    
    invalid_urls = [link['url'] for link in links_info if link['url'] not in [vl['url'] for vl in valid_links]]
    for url in invalid_urls:
        print(f"❌ {url}")
    
    return valid_links

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_ai_link_validator.py <url> [base_url]")
        print("  或: python test_ai_link_validator.py --batch <url1> <url2> ... [--base-url <base_url>]")
        sys.exit(1)
    
    # 检查是否为批量模式
    if sys.argv[1] == "--batch":
        urls = []
        base_url = None
        
        # 解析命令行参数
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--base-url":
                if i+1 < len(sys.argv):
                    base_url = sys.argv[i+1]
                    i += 2
                else:
                    print("错误: --base-url 参数需要提供一个值")
                    sys.exit(1)
            else:
                urls.append(sys.argv[i])
                i += 1
        
        if not urls:
            print("错误: 批量模式需要至少提供一个URL")
            sys.exit(1)
            
        test_batch_links(urls, base_url)
    else:
        # 单链接模式
        url = sys.argv[1]
        base_url = sys.argv[2] if len(sys.argv) > 2 else None
        
        test_single_link(url, base_url) 