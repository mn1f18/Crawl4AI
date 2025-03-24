import requests

# 指定要测试的链接索引
data = {'index': 3}

# 发送POST请求到Flask应用的/crawl端点
response = requests.post('http://127.0.0.1:5000/crawl', json=data)

# 打印返回的HTML内容
print(response.text)