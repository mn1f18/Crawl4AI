import requests

# 指定要测试的链接索引列表
indices = list(range(1, 3))  # 只爬取第1和第2个网页

# 是否使用 ds 接口
use_ds_interface = False  # 设置为 True 使用 ds 接口

# 发送POST请求到Flask应用的/crawl端点
for index in indices:
    response = requests.post('http://127.0.0.1:5000/crawl', json={'index': index, 'use_ds': use_ds_interface})
    # 打印返回的HTML内容
    print(f"Index {index}:")
    print(response.text)
    print("-" * 40)