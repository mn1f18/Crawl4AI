import os
import json
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
import openai
from bs4 import BeautifulSoup

# 导入prompt配置
try:
    from backend.ds_prompt_config import LINK_VALIDATION_PROMPT, BATCH_LINK_VALIDATION_PROMPT
except ImportError:
    try:
        from ds_prompt_config import LINK_VALIDATION_PROMPT, BATCH_LINK_VALIDATION_PROMPT
    except ImportError:
        # 默认prompt配置
        LINK_VALIDATION_PROMPT = """
        你是一个专门判断链接是否为有效农业新闻链接的AI助手。请评估以下链接：
        
        URL: {url}
        链接文本: {link_text}
        URL路径: {url_path}
        
        请判断此链接是否为有效新闻链接，并给出0-100的分数。
        有效新闻链接特征:
        - 链接指向具体新闻文章而非主页或栏目页
        - URL结构通常包含日期或文章标识符
        - 链接文本看起来像新闻标题
        - 通常不包含tag、login、search等非文章路径
        
        请直接返回以下JSON格式结果:
        {{"score": 分数值(0-100), "is_valid": true/false, "reason": "简要分析原因"}}
        """
        
        BATCH_LINK_VALIDATION_PROMPT = """
        请判断以下链接列表中哪些是有效的农业新闻链接:
        
        {links_json}
        
        对每个链接评估，给出0-100分数，并标记是否有效。
        有效新闻链接:
        - 指向具体文章页面
        - 通常有文章标识符或日期
        - 不是tag、类别、搜索页面
        
        直接返回JSON列表:
        [
          {{"url": "链接1", "score": 分数值, "is_valid": true/false}},
          {{"url": "链接2", "score": 分数值, "is_valid": true/false}},
          ...
        ]
        """

# 配置DeepSeek API
openai.api_key = "sk-86b89a0e6b024d03a2421cf5bf7e2d82"
openai.base_url = "https://api.deepseek.com/v1"

# 创建客户端
client = openai.OpenAI(
    api_key = "sk-86b89a0e6b024d03a2421cf5bf7e2d82",
    base_url = "https://api.deepseek.com/v1"
)

# 配置选项
ENABLE_LOGGING = True                # 是否记录AI判断结果
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_link_decisions.jsonl") # 日志文件路径
VALID_SCORE_THRESHOLD = 60           # 有效链接分数阈值
MAX_BATCH_SIZE = 5                   # 批量验证的最大链接数

# 链接判断结果缓存
url_judgment_cache = {}

def extract_basic_features(url, a_tag=None):
    """
    从URL和链接标签中提取最基本的特征
    
    参数:
        url: 待检查的URL
        a_tag: 可选的链接标签对象
    
    返回:
        包含提取特征的字典
    """
    # 解析URL
    parsed = urlparse(url)
    
    # 提取基本特征
    features = {
        "url": url,
        "url_path": parsed.path,
        "link_text": a_tag.get_text().strip() if a_tag else ""
    }
    
    return features

def log_link_decision(url, is_valid, score, reason=""):
    """记录链接判断结果"""
    if not ENABLE_LOGGING:
        return
        
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            decision = {
                "url": url,
                "is_valid": is_valid,
                "score": score,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"记录链接判断结果时出错: {e}")

def is_valid_news_link_with_ai(link, base_url, a_tag=None, html_content=None):
    """
    使用DeepSeek AI判断链接是否为有效新闻链接
    
    参数:
        link: 待检查的链接
        base_url: 基础URL
        a_tag: 可选的链接标签
        html_content: 可选的HTML内容（此版本未使用）
    
    返回:
        布尔值，指示链接是否有效
    """
    try:
        # 基础过滤 - 明显的非新闻链接
        if not link or not isinstance(link, str):
            print(f"  ❌ 跳过无效链接格式: {link}")
            return False
            
        if link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            print(f"  ❌ 跳过特殊协议链接: {link}")
            return False
            
        # 构建完整URL
        if not urlparse(link).netloc:
            full_url = urljoin(base_url, link)
        else:
            full_url = link
            
        # 检查缓存
        if full_url in url_judgment_cache:
            is_valid = url_judgment_cache[full_url]
            print(f"  {'✅' if is_valid else '❌'} 缓存结果: {full_url} {'有效' if is_valid else '无效'}")
            return is_valid
            
        # 排除媒体文件
        if any(urlparse(full_url).path.lower().endswith(ext) for ext in 
              ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.doc', '.css', '.js']):
            print(f"  ❌ 跳过媒体/资源文件: {full_url}")
            url_judgment_cache[full_url] = False
            return False
        
        # 提取特征
        print(f"  🔍 提取链接特征: {full_url}")
        features = extract_basic_features(full_url, a_tag)
        link_text = features["link_text"]
        if link_text:
            print(f"  📝 链接文本: \"{link_text[:50]}{'...' if len(link_text) > 50 else ''}\"")
        
        # 使用prompt模板
        prompt = LINK_VALIDATION_PROMPT.format(
            url=features["url"],
            link_text=features["link_text"],
            url_path=features["url_path"]
        )
        
        try:
            # 调用DeepSeek API
            print(f"  📤 发送验证请求到DeepSeek API...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # 解析结果
            print(f"  📥 收到DeepSeek API响应，解析中...")
            answer = response.choices[0].message.content
            
            try:
                # 尝试解析JSON响应
                # 清理可能的Markdown代码块语法
                cleaned_answer = answer
                if "```json" in answer:
                    # 提取代码块内容
                    cleaned_answer = re.search(r'```json\s*(.*?)\s*```', answer, re.DOTALL)
                    if cleaned_answer:
                        cleaned_answer = cleaned_answer.group(1).strip()
                    else:
                        # 如果正则匹配失败，尝试简单删除标记
                        cleaned_answer = answer.replace("```json", "").replace("```", "").strip()
                
                # 尝试解析JSON
                result = json.loads(cleaned_answer)
                
                score = result.get("score", 0)
                is_valid = result.get("is_valid", False)
                reason = result.get("reason", "")
                
                # 记录判断结果
                log_link_decision(full_url, is_valid, score, reason)
                
                # 缓存结果
                url_judgment_cache[full_url] = is_valid
                
                print(f"  {'✅' if is_valid else '❌'} AI判断结果: {full_url} {'有效' if is_valid else '无效'} (分数: {score})")
                if reason:
                    print(f"  💡 判断理由: {reason}")
                
                return is_valid
                
            except json.JSONDecodeError:
                print(f"  ⚠️ 无法解析AI响应为JSON，尝试直接提取分数...")
                print(f"  🔍 原始响应: {answer[:100]}...")
                # 尝试从文本中提取分数
                score_match = re.search(r'score"?\s*:\s*(\d+)', answer)
                if score_match:
                    score = int(score_match.group(1))
                    is_valid = score >= VALID_SCORE_THRESHOLD
                    url_judgment_cache[full_url] = is_valid
                    print(f"  {'✅' if is_valid else '❌'} 从文本提取的分数: {score}，结果: {'有效' if is_valid else '无效'}")
                    return is_valid
                
                # 如果无法提取，默认返回False
                print(f"  ❌ 无法从响应中提取结果，默认为无效")
                url_judgment_cache[full_url] = False
                return False
                
        except Exception as e:
            print(f"  ⚠️ 调用DeepSeek API时出错: {str(e)}")
            # 直接返回结果
            url_judgment_cache[full_url] = False
            return False
            
    except Exception as e:
        print(f"  ⚠️ AI判断链接时出错: {str(e)}, 链接: {link}")
        return False

def batch_link_validation(links_info, base_url, html_content=None):
    """
    批量验证链接，优化API调用频率
    
    参数:
        links_info: 字典列表，每个字典包含 'url', 'a_tag', 'title' 键
        base_url: 基础URL
        html_content: 可选的HTML内容
    
    返回:
        列表，包含判定为有效的链接信息
    """
    valid_links = []
    
    # 预筛选 - 基础规则过滤明显无效的链接
    filtered_links = []
    
    print(f"🔍 开始筛选 {len(links_info)} 个链接...")
    for link_info in links_info:
        # 统一处理url键
        url = None
        if 'url' in link_info:
            url = link_info['url']
        elif 'link' in link_info:
            url = link_info['link']
            # 统一为url键
            link_info['url'] = url
        
        # 跳过空链接或非字符串链接
        if not url or not isinstance(url, str):
            continue
            
        # 跳过非HTTP链接
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
            
        # 构建完整URL
        if not urlparse(url).netloc:
            full_url = urljoin(base_url, url)
        else:
            full_url = url
            
        # 更新为完整URL
        link_info['url'] = full_url
            
        # 检查缓存
        if full_url in url_judgment_cache:
            if url_judgment_cache[full_url]:
                link_info['is_valid'] = True
                link_info['ai_score'] = 80  # 默认分数
                link_info['ai_reason'] = "缓存验证通过"
                valid_links.append(link_info)
            continue
            
        # 排除媒体文件
        if any(urlparse(full_url).path.lower().endswith(ext) for ext in 
              ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.doc', '.css', '.js']):
            url_judgment_cache[full_url] = False
            continue
            
        # 添加到待处理列表
        filtered_links.append(link_info)
    
    # 如果没有链接需要验证，直接返回
    if not filtered_links:
        print("⚠️ 基础筛选后没有链接需要AI验证")
        # 关键修改：如果没有链接需要验证，返回已验证通过的链接
        return valid_links
    
    print(f"✅ 基础筛选后有 {len(filtered_links)} 个链接需要AI验证")
    
    # 处理未缓存的链接
    # 分批处理，每批最多MAX_BATCH_SIZE个链接
    batch_count = (len(filtered_links) + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE  # 向上取整计算批次数
    print(f"🔄 将分 {batch_count} 批进行AI验证，每批最多 {MAX_BATCH_SIZE} 个链接")
    
    for i in range(0, len(filtered_links), MAX_BATCH_SIZE):
        batch = filtered_links[i:i+MAX_BATCH_SIZE]
        current_batch = i // MAX_BATCH_SIZE + 1
        print(f"🧠 正在验证第 {current_batch}/{batch_count} 批，包含 {len(batch)} 个链接...")
        
        if len(batch) == 1:
            # 单链接处理
            link_info = batch[0]
            print(f"  - 验证单个链接: {link_info['url']}")
            if is_valid_news_link_with_ai(link_info['url'], base_url, link_info.get('a_tag')):
                # 添加验证信息
                link_info['is_valid'] = True
                link_info['ai_score'] = 80  # 默认分数
                link_info['ai_reason'] = "AI验证通过"
                valid_links.append(link_info)
                print(f"  ✅ 链接有效: {link_info['url']}")
            else:
                print(f"  ❌ 链接无效: {link_info['url']}")
        else:
            # 批量处理
            try:
                # 准备批量处理的链接数据
                links_data = []
                for link_info in batch:
                    links_data.append({
                        "url": link_info['url'],
                        "text": link_info.get('title', '') or (link_info.get('a_tag').get_text().strip() if link_info.get('a_tag') else '')
                    })
                
                # 构建批量验证prompt
                prompt = BATCH_LINK_VALIDATION_PROMPT.format(
                    links_json=json.dumps(links_data, ensure_ascii=False)
                )
                
                print(f"  📤 发送批量验证请求到DeepSeek API...")
                # 调用DeepSeek API（更新为新版本API）
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                print(f"  📥 收到DeepSeek API响应，正在解析...")
                # 解析结果 (更新为新版本API的响应格式)
                answer = response.choices[0].message.content
                
                try:
                    # 尝试解析JSON响应 (增强处理Markdown代码块的能力)
                    # 清理可能的Markdown代码块语法
                    cleaned_answer = answer
                    if "```json" in answer:
                        # 提取代码块内容
                        cleaned_answer = re.search(r'```json\s*(.*?)\s*```', answer, re.DOTALL)
                        if cleaned_answer:
                            cleaned_answer = cleaned_answer.group(1).strip()
                        else:
                            # 如果正则匹配失败，尝试简单删除标记
                            cleaned_answer = answer.replace("```json", "").replace("```", "").strip()
                    
                    # 尝试解析JSON
                    result = json.loads(cleaned_answer)
                    
                    # 处理批量结果
                    valid_count = 0
                    for item in result:
                        url = item.get("url")
                        is_valid = item.get("is_valid", False)
                        score = item.get("score", 0)
                        reason = item.get("reason", "")
                        
                        # 缓存结果
                        url_judgment_cache[url] = is_valid
                        
                        # 如果有效，添加到结果列表
                        if is_valid:
                            valid_count += 1
                            # 找到对应的link_info
                            for link_info in batch:
                                if link_info['url'] == url:
                                    # 添加验证信息
                                    link_info['is_valid'] = True
                                    link_info['ai_score'] = score
                                    link_info['ai_reason'] = reason or "AI验证通过"
                                    valid_links.append(link_info)
                                    print(f"  ✅ 链接有效 (分数: {score}): {url}")
                                    break
                        else:
                            print(f"  ❌ 链接无效 (分数: {score}): {url}")
                        
                        # 记录日志
                        log_link_decision(url, is_valid, score, reason)
                    
                    print(f"  📊 批次结果: {valid_count}/{len(batch)} 个有效链接")
                        
                except json.JSONDecodeError:
                    print(f"  ⚠️ 无法解析批量验证响应为JSON: {answer}")
                    print(f"  🔄 回退到逐个验证...")
                    # 回退到逐个验证
                    for idx, link_info in enumerate(batch):
                        print(f"    🔍 验证链接 {idx+1}/{len(batch)}: {link_info['url']}")
                        is_valid = is_valid_news_link_with_ai(link_info['url'], base_url, link_info.get('a_tag'))
                        if is_valid:
                            # 添加验证信息
                            link_info['is_valid'] = True
                            link_info['ai_score'] = 80  # 默认分数
                            link_info['ai_reason'] = "单独AI验证通过"
                            valid_links.append(link_info)
                            print(f"    ✅ 链接有效: {link_info['url']}")
                        else:
                            print(f"    ❌ 链接无效: {link_info['url']}")
                            
            except Exception as e:
                print(f"  ⚠️ 批量验证出错: {e}")
                print(f"  🔄 回退到逐个验证...")
                # 回退到逐个验证
                for idx, link_info in enumerate(batch):
                    print(f"    🔍 验证链接 {idx+1}/{len(batch)}: {link_info['url']}")
                    is_valid = is_valid_news_link_with_ai(link_info['url'], base_url, link_info.get('a_tag'))
                    if is_valid:
                        # 添加验证信息
                        link_info['is_valid'] = True
                        link_info['ai_score'] = 80  # 默认分数
                        link_info['ai_reason'] = "单独AI验证通过"
                        valid_links.append(link_info)
                        print(f"    ✅ 链接有效: {link_info['url']}")
                    else:
                        print(f"    ❌ 链接无效: {link_info['url']}")
    
    print(f"🏁 AI验证完成，总共有 {len(valid_links)}/{len(links_info)} 个有效链接")
    return valid_links

# 导出函数
__all__ = ['is_valid_news_link_with_ai', 'batch_link_validation'] 