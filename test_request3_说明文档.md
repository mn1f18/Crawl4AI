# test_request3.py 说明文档

## 项目概述

`test_request3.py` 是一个专门用于抓取和处理农业新闻网站内容的Python爬虫脚本。它使用AI技术对新闻链接进行验证，筛选出有效的新闻文章，并抓取其内容。脚本将结果保存到Excel文件中，同时维护历史链接数据库以避免重复抓取。

## 主要功能

1. **多源抓取**：从Excel文件中读取多个新闻源的URL，进行批量抓取
2. **AI链接验证**：使用AI（DeepSeek API）鉴别链接是否为有效新闻文章
3. **内容过滤**：使用`PruningContentFilter`过滤无用内容
4. **历史链接管理**：维护已知链接数据库，避免重复处理
5. **数据导出**：将抓取结果和历史链接数据导出到Excel文件
6. **调试模式**：支持单个链接的调试

## 系统架构

该脚本基于以下技术和库：

- **爬虫引擎**：`crawl4ai`库提供的`AsyncWebCrawler`
- **HTML解析**：BeautifulSoup4
- **内容抽取**：自定义标题、日期提取算法
- **AI验证**：外部AI链接验证模块
- **异步处理**：asyncio
- **数据存储**：JSON文件（历史链接）和Excel文件（结果）

## 配置选项

脚本开头定义了多个配置选项，可以根据需要进行调整：

```python
# 配置选项
SAVE_TO_EXCEL = True                # 是否保存结果到Excel
MAX_LINKS_PER_SOURCE = 100          # 每个来源最多抓取的链接数
MIN_CONTENT_LENGTH = 300            # 最小有效内容长度
MAX_RETRY_COUNT = 2                 # 链接请求失败时最大重试次数
REQUEST_TIMEOUT = 60                # 请求超时时间（秒）
SKIP_EXISTING_LINKS = True          # 是否跳过已存在的链接
LINKS_HISTORY_DIR = ...             # 历史链接存储目录
USE_AI_LINK_VALIDATION = True       # 是否使用AI链接验证
USE_COLD_START = False              # 是否使用冷启动模式（跳过AI验证）
```

## 主要流程

### 1. 初始化和配置加载

- 加载必要的库和模块
- 检查AI链接验证模块可用性
- 确保历史链接目录存在
- 读取源文件（Excel格式）

### 2. 链接获取和验证

1. 遍历Excel文件中的每个新闻源
2. 爬取主页HTML内容
3. 提取所有链接
4. 与历史链接数据比对，识别新链接
5. 使用AI验证新链接是否为有效新闻
6. 更新链接历史记录

### 3. 内容抓取

1. 对AI验证为有效的链接进行内容抓取
2. 提取文章标题、发布日期等元数据
3. 提取正文内容
4. 生成内容摘要和指纹
5. 更新链接历史记录

### 4. 结果处理

1. 将抓取结果写入Excel文件
2. 导出历史链接数据到Excel文件
3. 输出统计信息

## AI链接验证详解

`test_request3.py`使用外部的`ai_link_validator.py`模块实现高精度的新闻链接判断，这是系统的核心特性之一。

### 验证原理

AI链接验证基于DeepSeek API的大型语言模型能力，通过分析链接URL结构、文本内容和上下文信息来判断链接是否指向有效的新闻文章。系统实现了两种验证模式：

1. **单链接验证**：`is_valid_news_link_with_ai`函数处理单个链接的验证
2. **批量验证**：`batch_link_validation`函数一次处理多个链接，优化API调用效率

### 验证流程

1. **预筛选**：首先通过基础规则过滤明显的非新闻链接（如媒体文件、特殊协议链接）
2. **特征提取**：分析URL结构、链接文本等特征
3. **AI评估**：调用DeepSeek API，使用专门设计的prompt进行评估
4. **结果解析**：解析API返回的JSON结果，提取评分和有效性判断
5. **结果缓存**：将验证结果缓存，避免重复验证

### 批量验证机制

系统实现了高效的批量验证机制，每次最多验证5个链接（由`MAX_BATCH_SIZE`配置控制）：

```python
# 处理过程摘要
filtered_links = []  # 经过基础规则过滤后的链接
batches = []  # 分批处理的链接组

# 将过滤后的链接分成多批
for i in range(0, len(filtered_links), MAX_BATCH_SIZE):
    batches.append(filtered_links[i:i+MAX_BATCH_SIZE])

# 批量处理每组链接
for idx, batch in enumerate(batches, 1):
    print(f"🧠 正在验证第 {idx}/{len(batches)} 批，包含 {len(batch)} 个链接...")
    # 调用DeepSeek API进行批量验证
    # ...
```

### 评分机制

AI验证系统为每个链接提供0-100的分数：

- **0-59分**：被判定为无效链接（主页、分类页、标签页等）
- **60-79分**：一般有效性，可能是新闻文章
- **80-100分**：高度确信是有效新闻文章

系统使用`VALID_SCORE_THRESHOLD=60`作为有效链接的阈值，这个值可以根据需要调整。

### Prompt设计

系统使用两个专门设计的prompt进行链接验证：

1. **单链接验证prompt**：针对单个链接的深入分析
```
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
{"score": 分数值(0-100), "is_valid": true/false, "reason": "简要分析原因"}
```

2. **批量验证prompt**：针对多个链接的批量处理
```
请判断以下链接列表中哪些是有效的农业新闻链接:

{links_json}

对每个链接评估，给出0-100分数，并标记是否有效。
有效新闻链接:
- 指向具体文章页面
- 通常有文章标识符或日期
- 不是tag、类别、搜索页面

直接返回JSON列表:
[
  {"url": "链接1", "score": 分数值, "is_valid": true/false},
  {"url": "链接2", "score": 分数值, "is_valid": true/false},
  ...
]
```

### 验证结果日志

系统会记录所有AI验证决策到`ai_link_decisions.jsonl`文件（JSONL格式），包含以下信息：

- 链接URL
- 验证时间
- 是否有效
- 评分
- 判断理由

这些日志对于后期分析和改进验证算法非常有价值。

## 内容抽取与过滤

`test_request3.py`使用多种技术来抽取和过滤新闻内容，确保获取高质量的文章文本。

### PruningContentFilter机制

系统集成了`crawl4ai`库的`PruningContentFilter`内容过滤器，该过滤器能智能识别并保留页面中最相关的内容：

```python
# 设置过滤器
prune_filter = PruningContentFilter(
    threshold=0.45,
    threshold_type="dynamic",
    min_word_threshold=5
)

# 设置Markdown生成器
md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

# 设置爬虫配置
crawler_config = CrawlerRunConfig(
    markdown_generator=md_generator,
    page_timeout=REQUEST_TIMEOUT * 1000,
    cache_mode=CacheMode.BYPASS
)
```

过滤机制主要特点：

- **动态阈值**：`threshold_type="dynamic"`使系统能根据内容特性自动调整阈值
- **词汇阈值**：`min_word_threshold=5`确保只保留包含至少5个词的内容块
- **噪音去除**：自动识别并移除导航、页脚、侧边栏等非内容区域

### 元数据提取

系统实现了多种高级元数据提取函数:

1. **标题提取**：`extract_title`函数通过多种方法提取文章标题
   - 检查`<title>`标签内容
   - 查找主要内容区域的标题标签(`h1`，`h2`)
   - 检查元数据标签(`og:title`, `twitter:title`等)
   - 从URL中提取可能的标题信息

2. **发布日期提取**：`extract_publish_date`函数通过多种方法提取发布日期
   - 检查元数据标签中的日期信息
   - 查找`<time>`标签
   - 使用特定CSS选择器查找日期元素
   - 在全文中通过正则表达式匹配日期格式

### 内容摘要和指纹生成

系统使用`evaluate_content_quality`函数生成内容摘要和指纹：

```python
def evaluate_content_quality(html_content, title, url=""):
    """简化版函数，不再评估内容质量，只返回内容摘要和指纹"""
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
    
    return True, content_summary, content_fingerprint
```

这一功能有两个主要作用：
- **内容摘要**：提供文章的前200个字符作为预览
- **内容指纹**：使用MD5哈希生成唯一标识，用于重复内容检测

## 链接验证逻辑

脚本使用多层级的验证逻辑来识别有效的新闻链接：

1. **基础过滤**：过滤掉明显的非新闻链接（如媒体文件、外部链接等）
2. **历史记录检查**：检查链接是否已存在于历史记录中
3. **AI验证**：使用DeepSeek API对链接进行验证，打分区分新闻文章和非文章页面

## 历史链接管理

脚本维护一个基于JSON的历史链接数据库，每个新闻源对应一个JSON文件，存储在`link_history`目录下。每条记录包含以下信息：

- URL和标题
- 有效性标记
- 首次发现和最后更新时间
- 内容长度和摘要
- 内容指纹（用于重复检测）
- AI验证分数和理由
- 爬取次数和状态

## 使用方法

### 正常模式

直接运行脚本进行完整爬取流程：

```
python test_request3.py
```

### 调试模式

用于测试单个链接的抓取：

```
python test_request3.py --debug <url> <source_name>
```

例如：

```
python test_request3.py --debug https://example.com/news/article123 source1
```

## 输出文件

脚本会生成两类Excel文件：

1. **抓取结果文件**：`news_results_时间戳.xlsx`
   - 包含所有成功抓取的新闻文章数据

2. **历史链接导出**：`links_history_时间戳.xlsx`
   - 包含所有历史链接记录

## 冷启动模式

设置`USE_COLD_START = True`可启用冷启动模式，该模式下：
- 跳过AI验证环节
- 所有新链接都被视为有效
- 直接进行内容抓取

这对于初始数据收集或AI服务不可用时很有用。

## 错误处理

脚本实现了全面的错误处理机制：
- 链接抓取失败时会进行重试（最多重试次数由`MAX_RETRY_COUNT`定义）
- 每个错误都会被记录在历史链接数据中
- 单个源的错误不会影响整体流程

## 扩展和定制

该脚本设计灵活，可通过多种方式进行扩展和定制：

### 添加新的来源

只需在Excel文件（默认为`testhomepage.xlsx`）中添加新行，包含以下信息：
- 备注名称
- 网站URL
- 来源ID

### 定制AI验证参数

可以修改`ai_link_validator.py`中的参数：
- 调整`VALID_SCORE_THRESHOLD`更改有效链接判断阈值
- 修改`MAX_BATCH_SIZE`更改每批验证的链接数量
- 调整验证prompt以适应不同类型的网站

### 调整内容过滤参数

可修改`PruningContentFilter`的参数以获取更精确的内容：
```python
prune_filter = PruningContentFilter(
    threshold=0.45,  # 可调整阈值
    threshold_type="dynamic",  # 可改为"static"
    min_word_threshold=5  # 可增大以过滤更多短内容
)
```

### 开发新的元数据提取器

系统内置的`extract_title`和`extract_publish_date`函数可扩展以适应特殊网站：
- 添加新的选择器规则以匹配特定网站结构
- 增加特定网站的处理逻辑
- 创建针对特定新闻源的专用提取器

### 集成其他AI服务

当前系统使用DeepSeek API，但可以扩展支持其他AI服务：
- 修改`ai_link_validator.py`以支持OpenAI、Claude等API
- 实现自定义分类器来替代云服务API
- 添加本地部署的模型支持

### 自定义输出格式

可以扩展当前的Excel输出，添加新的导出格式：
- 开发JSON或CSV导出功能
- 添加数据库存储支持
- 实现API接口提供爬取结果 