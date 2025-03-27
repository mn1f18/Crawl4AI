# ds_prompt_config.py

# 示例 prompt 配置
DS_PROMPT_SETTINGS = {
    'default_prompt': 'Analyze the content and provide insights.',
    'detailed_analysis': 'Provide a detailed analysis of the content, focusing on key themes and insights.'
}

# 链接有效性评估 prompt (简洁版)
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

# 批量链接验证 prompt
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

# 其他 prompt 配置可以根据需要添加 