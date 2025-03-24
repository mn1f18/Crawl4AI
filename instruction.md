# 启动步骤和查看结果

## 启动步骤
1. 确保你已经安装了所有必要的依赖包。
2. 在终端中导航到项目的 `backend` 目录。
3. 运行命令 `python app.py` 启动Flask应用。

## 查看结果
- 访问 `http://127.0.0.1:5000/view_result?type=content` 查看爬取的具体内容。
- 访问 `http://127.0.0.1:5000/view_result?type=title` 查看爬取的标题。
- 访问 `http://127.0.0.1:5000/view_result?type=link` 查看爬取的链接。

---

项目链接：
https://github.com/mn1f18/Crawl4AI.git

项目测试方式：
后端接口的方式，输出新闻结果

🚀🤖 Crawl4AI: Open-Source LLM-Friendly Web Crawler & Scraper
unclecode%2Fcrawl4ai | Trendshift
参考的项目官方网站：
https://docs.crawl4ai.com/


GitHub Stars GitHub Forks PyPI version

Python Version Downloads License

Crawl4AI is the #1 trending GitHub repository, actively maintained by a vibrant community. It delivers blazing-fast, AI-ready web crawling tailored for large language models, AI agents, and data pipelines. Fully open source, flexible, and built for real-time performance, Crawl4AI empowers developers with unmatched speed, precision, and deployment ease.

Note: If you're looking for the old documentation, you can access it here.

Quick Start
Here's a quick example to show you how easy it is to use Crawl4AI with its asynchronous capabilities:

import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://crawl4ai.com")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())
What Does Crawl4AI Do?
Crawl4AI is a feature-rich crawler and scraper that aims to:

1. Generate Clean Markdown: Perfect for RAG pipelines or direct ingestion into LLMs.
2. Structured Extraction: Parse repeated patterns with CSS, XPath, or LLM-based extraction.
3. Advanced Browser Control: Hooks, proxies, stealth modes, session re-use—fine-grained control.
4. High Performance: Parallel crawling, chunk-based extraction, real-time use cases.
5. Open Source: No forced API keys, no paywalls—everyone can access their data.

Core Philosophies: - Democratize Data: Free to use, transparent, and highly configurable.
- LLM Friendly: Minimally processed, well-structured text, images, and metadata, so AI models can easily consume it.

Documentation Structure
To help you get started, we've organized our docs into clear sections:

Setup & Installation
Basic instructions to install Crawl4AI via pip or Docker.
Quick Start
A hands-on introduction showing how to do your first crawl, generate Markdown, and do a simple extraction.
Core
Deeper guides on single-page crawling, advanced browser/crawler parameters, content filtering, and caching.
Advanced
Explore link & media handling, lazy loading, hooking & authentication, proxies, session management, and more.
Extraction
Detailed references for no-LLM (CSS, XPath) vs. LLM-based strategies, chunking, and clustering approaches.
API Reference
Find the technical specifics of each class and method, including AsyncWebCrawler, arun(), and CrawlResult.
Throughout these sections, you'll find code samples you can copy-paste into your environment. If something is missing or unclear, raise an issue or PR.

How You Can Support
Star & Fork: If you find Crawl4AI helpful, star the repo on GitHub or fork it to add your own features.
File Issues: Encounter a bug or missing feature? Let us know by filing an issue, so we can improve.
Pull Requests: Whether it's a small fix, a big feature, or better docs—contributions are always welcome.
Join Discord: Come chat about web scraping, crawling tips, or AI workflows with the community.
Spread the Word: Mention Crawl4AI in your blog posts, talks, or on social media.
Our mission: to empower everyone—students, researchers, entrepreneurs, data scientists—to access, parse, and shape the world's data with speed, cost-efficiency, and creative freedom.

nstallation & Setup (2023 Edition)
1. Basic Installation
pip install crawl4ai
This installs the core Crawl4AI library along with essential dependencies. No advanced features (like transformers or PyTorch) are included yet.

2. Initial Setup & Diagnostics
2.1 Run the Setup Command
After installing, call:

crawl4ai-setup
What does it do? - Installs or updates required Playwright browsers (Chromium, Firefox, etc.) - Performs OS-level checks (e.g., missing libs on Linux) - Confirms your environment is ready to crawl

2.2 Diagnostics
Optionally, you can run diagnostics to confirm everything is functioning:

crawl4ai-doctor
This command attempts to: - Check Python version compatibility - Verify Playwright installation - Inspect environment variables or library conflicts

If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run crawl4ai-setup.

3. Verifying Installation: A Simple Crawl (Skip this step if you already run crawl4ai-doctor)
Below is a minimal Python script demonstrating a basic crawl. It uses our new BrowserConfig and CrawlerRunConfig for clarity, though no custom settings are passed in this example:

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
        )
        print(result.markdown[:300])  # Show the first 300 characters of extracted text

if __name__ == "__main__":
    asyncio.run(main())
Expected outcome: - A headless browser session loads example.com - Crawl4AI returns ~300 characters of markdown.
If errors occur, rerun crawl4ai-doctor or manually ensure Playwright is installed correctly.

4. Advanced Installation (Optional)
Warning: Only install these if you truly need them. They bring in larger dependencies, including big models, which can increase disk usage and memory load significantly.

4.1 Torch, Transformers, or All
Text Clustering (Torch)

pip install crawl4ai[torch]
crawl4ai-setup
Installs PyTorch-based features (e.g., cosine similarity or advanced semantic chunking).
Transformers

pip install crawl4ai[transformer]
crawl4ai-setup
Adds Hugging Face-based summarization or generation strategies.
All Features

pip install crawl4ai[all]
crawl4ai-setup
(Optional) Pre-Fetching Models
crawl4ai-download-models
This step caches large models locally (if needed). Only do this if your workflow requires them.
5. Docker (Experimental)
We provide a temporary Docker approach for testing. It's not stable and may break with future releases. We plan a major Docker revamp in a future stable version, 2025 Q1. If you still want to try:

docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
You can then make POST requests to http://localhost:11235/crawl to perform crawls. Production usage is discouraged until our new Docker approach is ready (planned in Jan or Feb 2025).

6. Local Server Mode (Legacy)
Some older docs mention running Crawl4AI as a local server. This approach has been partially replaced by the new Docker-based prototype and upcoming stable server release. You can experiment, but expect major changes. Official local server instructions will arrive once the new Docker architecture is finalized.

Summary
1. Install with pip install crawl4ai and run crawl4ai-setup. 2. Diagnose with crawl4ai-doctor if you see errors. 3. Verify by crawling example.com with minimal BrowserConfig + CrawlerRunConfig. 4. Advanced features (Torch, Transformers) are optional—avoid them if you don't need them (they significantly increase resource usage). 5. Docker is experimental—use at your own risk until the stable version is released. 6. Local server references in older docs are largely deprecated; a new solution is in progress.

Docker Deployment
Crawl4AI provides official Docker images for easy deployment and scalability. This guide covers installation, configuration, and usage of Crawl4AI in Docker environments.

Quick Start 🚀
Pull and run the basic version:

# Basic run without security
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic

# Run with API security enabled
docker run -p 11235:11235 -e CRAWL4AI_API_TOKEN=your_secret_token unclecode/crawl4ai:basic
Running with Docker Compose 🐳
Use Docker Compose (From Local Dockerfile or Docker Hub)
Crawl4AI provides flexibility to use Docker Compose for managing your containerized services. You can either build the image locally from the provided Dockerfile or use the pre-built image from Docker Hub.

Option 1: Using Docker Compose to Build Locally
If you want to build the image locally, use the provided docker-compose.local.yml file.

docker-compose -f docker-compose.local.yml up -d
This will: 1. Build the Docker image from the provided Dockerfile. 2. Start the container and expose it on http://localhost:11235.

Option 2: Using Docker Compose with Pre-Built Image from Hub
If you prefer using the pre-built image on Docker Hub, use the docker-compose.hub.yml file.

docker-compose -f docker-compose.hub.yml up -d
This will: 1. Pull the pre-built image unclecode/crawl4ai:basic (or all, depending on your configuration). 2. Start the container and expose it on http://localhost:11235.

Stopping the Running Services
To stop the services started via Docker Compose, you can use:

docker-compose -f docker-compose.local.yml down
# OR
docker-compose -f docker-compose.hub.yml down
If the containers don't stop and the application is still running, check the running containers:

docker ps
Find the CONTAINER ID of the running service and stop it forcefully:

docker stop <CONTAINER_ID>
Debugging with Docker Compose
Check Logs: To view the container logs:

docker-compose -f docker-compose.local.yml logs -f
Remove Orphaned Containers: If the service is still running unexpectedly:

docker-compose -f docker-compose.local.yml down --remove-orphans
Manually Remove Network: If the network is still in use:

docker network ls
docker network rm crawl4ai_default
Why Use Docker Compose?
Docker Compose is the recommended way to deploy Crawl4AI because: 1. It simplifies multi-container setups. 2. Allows you to define environment variables, resources, and ports in a single file. 3. Makes it easier to switch between local development and production-ready images.

For example, your docker-compose.yml could include API keys, token settings, and memory limits, making deployment quick and consistent.

API Security 🔒
Understanding CRAWL4AI_API_TOKEN
The CRAWL4AI_API_TOKEN provides optional security for your Crawl4AI instance:

If CRAWL4AI_API_TOKEN is set: All API endpoints (except /health) require authentication
If CRAWL4AI_API_TOKEN is not set: The API is publicly accessible
# Secured Instance
docker run -p 11235:11235 -e CRAWL4AI_API_TOKEN=your_secret_token unclecode/crawl4ai:all

# Unsecured Instance
docker run -p 11235:11235 unclecode/crawl4ai:all
Making API Calls
For secured instances, include the token in all requests:

import requests

# Setup headers if token is being used
api_token = "your_secret_token"  # Same token set in CRAWL4AI_API_TOKEN
headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}

# Making authenticated requests
response = requests.post(
    "http://localhost:11235/crawl",
    headers=headers,
    json={
        "urls": "https://example.com",
        "priority": 10
    }
)

# Checking task status
task_id = response.json()["task_id"]
status = requests.get(
    f"http://localhost:11235/task/{task_id}",
    headers=headers
)
Using with Docker Compose
In your docker-compose.yml:

services:
  crawl4ai:
    image: unclecode/crawl4ai:all
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN:-}  # Optional
    # ... other configuration
Then either: 1. Set in .env file:

CRAWL4AI_API_TOKEN=your_secret_token
Or set via command line:
CRAWL4AI_API_TOKEN=your_secret_token docker-compose up
Security Note: If you enable the API token, make sure to keep it secure and never commit it to version control. The token will be required for all API endpoints except the health check endpoint (/health).

Configuration Options 🔧
Environment Variables
You can configure the service using environment variables:

# Basic configuration
docker run -p 11235:11235 \
    -e MAX_CONCURRENT_TASKS=5 \
    unclecode/crawl4ai:all

# With security and LLM support
docker run -p 11235:11235 \
    -e CRAWL4AI_API_TOKEN=your_secret_token \
    -e OPENAI_API_KEY=sk-... \
    -e ANTHROPIC_API_KEY=sk-ant-... \
    unclecode/crawl4ai:all
Using Docker Compose (Recommended) 🐳
Create a docker-compose.yml:

version: '3.8'

services:
  crawl4ai:
    image: unclecode/crawl4ai:all
    ports:
      - "11235:11235"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN:-}  # Optional API security
      - MAX_CONCURRENT_TASKS=5
      # LLM Provider Keys
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    volumes:
      - /dev/shm:/dev/shm
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G
You can run it in two ways:

Using environment variables directly:

CRAWL4AI_API_TOKEN=secret123 OPENAI_API_KEY=sk-... docker-compose up
Using a .env file (recommended): Create a .env file in the same directory:

# API Security (optional)
CRAWL4AI_API_TOKEN=your_secret_token

# LLM Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Other Configuration
MAX_CONCURRENT_TASKS=5
Then simply run:

docker-compose up
Testing the Deployment 🧪
import requests

# For unsecured instances
def test_unsecured():
    # Health check
    health = requests.get("http://localhost:11235/health")
    print("Health check:", health.json())

    # Basic crawl
    response = requests.post(
        "http://localhost:11235/crawl",
        json={
            "urls": "https://www.nbcnews.com/business",
            "priority": 10
        }
    )
    task_id = response.json()["task_id"]
    print("Task ID:", task_id)

# For secured instances
def test_secured(api_token):
    headers = {"Authorization": f"Bearer {api_token}"}

    # Basic crawl with authentication
    response = requests.post(
        "http://localhost:11235/crawl",
        headers=headers,
        json={
            "urls": "https://www.nbcnews.com/business",
            "priority": 10
        }
    )
    task_id = response.json()["task_id"]
    print("Task ID:", task_id)
LLM Extraction Example 🤖
When you've configured your LLM provider keys (via environment variables or .env), you can use LLM extraction:

request = {
    "urls": "https://example.com",
    "extraction_config": {
        "type": "llm",
        "params": {
            "provider": "openai/gpt-4",
            "instruction": "Extract main topics from the page"
        }
    }
}

# Make the request (add headers if using API security)
response = requests.post("http://localhost:11235/crawl", json=request)
Note: Remember to add .env to your .gitignore to keep your API keys secure!

Usage Examples 📝
Basic Crawling
request = {
    "urls": "https://www.nbcnews.com/business",
    "priority": 10
}

response = requests.post("http://localhost:11235/crawl", json=request)
task_id = response.json()["task_id"]

# Get results
result = requests.get(f"http://localhost:11235/task/{task_id}")
Structured Data Extraction
schema = {
    "name": "Crypto Prices",
    "baseSelector": ".cds-tableRow-t45thuk",
    "fields": [
        {
            "name": "crypto",
            "selector": "td:nth-child(1) h2",
            "type": "text",
        },
        {
            "name": "price",
            "selector": "td:nth-child(2)",
            "type": "text",
        }
    ],
}

request = {
    "urls": "https://www.coinbase.com/explore",
    "extraction_config": {
        "type": "json_css",
        "params": {"schema": schema}
    }
}
Dynamic Content Handling
request = {
    "urls": "https://www.nbcnews.com/business",
    "js_code": [
        "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
    ],
    "wait_for": "article.tease-card:nth-child(10)"
}
AI-Powered Extraction (Full Version)
request = {
    "urls": "https://www.nbcnews.com/business",
    "extraction_config": {
        "type": "cosine",
        "params": {
            "semantic_filter": "business finance economy",
            "word_count_threshold": 10,
            "max_dist": 0.2,
            "top_k": 3
        }
    }
}
Platform-Specific Instructions 💻
macOS
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
Ubuntu
# Basic version
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic

# With GPU support
docker pull unclecode/crawl4ai:gpu
docker run --gpus all -p 11235:11235 unclecode/crawl4ai:gpu
Windows (PowerShell)
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
Testing 🧪
Save this as test_docker.py:

import requests
import json
import time
import sys

class Crawl4AiTester:
    def __init__(self, base_url: str = "http://localhost:11235"):
        self.base_url = base_url

    def submit_and_wait(self, request_data: dict, timeout: int = 300) -> dict:
        # Submit crawl job
        response = requests.post(f"{self.base_url}/crawl", json=request_data)
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")

        # Poll for result
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timeout")

            result = requests.get(f"{self.base_url}/task/{task_id}")
            status = result.json()

            if status["status"] == "completed":
                return status

            time.sleep(2)

def test_deployment():
    tester = Crawl4AiTester()

    # Test basic crawl
    request = {
        "urls": "https://www.nbcnews.com/business",
        "priority": 10
    }

    result = tester.submit_and_wait(request)
    print("Basic crawl successful!")
    print(f"Content length: {len(result['result']['markdown'])}")

if __name__ == "__main__":
    test_deployment()
Advanced Configuration ⚙️
Crawler Parameters
The crawler_params field allows you to configure the browser instance and crawling behavior. Here are key parameters you can use:

request = {
    "urls": "https://example.com",
    "crawler_params": {
        # Browser Configuration
        "headless": True,                    # Run in headless mode
        "browser_type": "chromium",          # chromium/firefox/webkit
        "user_agent": "custom-agent",        # Custom user agent
        "proxy": "http://proxy:8080",        # Proxy configuration

        # Performance & Behavior
        "page_timeout": 30000,               # Page load timeout (ms)
        "verbose": True,                     # Enable detailed logging
        "semaphore_count": 5,               # Concurrent request limit

        # Anti-Detection Features
        "simulate_user": True,               # Simulate human behavior
        "magic": True,                       # Advanced anti-detection
        "override_navigator": True,          # Override navigator properties

        # Session Management
        "user_data_dir": "./browser-data",   # Browser profile location
        "use_managed_browser": True,         # Use persistent browser
    }
}
Extra Parameters
The extra field allows passing additional parameters directly to the crawler's arun function:

request = {
    "urls": "https://example.com",
    "extra": {
        "word_count_threshold": 10,          # Min words per block
        "only_text": True,                   # Extract only text
        "bypass_cache": True,                # Force fresh crawl
        "process_iframes": True,             # Include iframe content
    }
}
Complete Examples
1. Advanced News Crawling

request = {
    "urls": "https://www.nbcnews.com/business",
    "crawler_params": {
        "headless": True,
        "page_timeout": 30000,
        "remove_overlay_elements": True      # Remove popups
    },
    "extra": {
        "word_count_threshold": 50,          # Longer content blocks
        "bypass_cache": True                 # Fresh content
    },
    "css_selector": ".article-body"
}
2. Anti-Detection Configuration

request = {
    "urls": "https://example.com",
    "crawler_params": {
        "simulate_user": True,
        "magic": True,
        "override_navigator": True,
        "user_agent": "Mozilla/5.0 ...",
        "headers": {
            "Accept-Language": "en-US,en;q=0.9"
        }
    }
}
3. LLM Extraction with Custom Parameters

request = {
    "urls": "https://openai.com/pricing",
    "extraction_config": {
        "type": "llm",
        "params": {
            "provider": "openai/gpt-4",
            "schema": pricing_schema
        }
    },
    "crawler_params": {
        "verbose": True,
        "page_timeout": 60000
    },
    "extra": {
        "word_count_threshold": 1,
        "only_text": True
    }
}
4. Session-Based Dynamic Content

request = {
    "urls": "https://example.com",
    "crawler_params": {
        "session_id": "dynamic_session",
        "headless": False,
        "page_timeout": 60000
    },
    "js_code": ["window.scrollTo(0, document.body.scrollHeight);"],
    "wait_for": "js:() => document.querySelectorAll('.item').length > 10",
    "extra": {
        "delay_before_return_html": 2.0
    }
}
5. Screenshot with Custom Timing

request = {
    "urls": "https://example.com",
    "screenshot": True,
    "crawler_params": {
        "headless": True,
        "screenshot_wait_for": ".main-content"
    },
    "extra": {
        "delay_before_return_html": 3.0
    }
}
Parameter Reference Table
Category	Parameter	Type	Description
Browser	headless	bool	Run browser in headless mode
Browser	browser_type	str	Browser engine selection
Browser	user_agent	str	Custom user agent string
Network	proxy	str	Proxy server URL
Network	headers	dict	Custom HTTP headers
Timing	page_timeout	int	Page load timeout (ms)
Timing	delay_before_return_html	float	Wait before capture
Anti-Detection	simulate_user	bool	Human behavior simulation
Anti-Detection	magic	bool	Advanced protection
Session	session_id	str	Browser session ID
Session	user_data_dir	str	Profile directory
Content	word_count_threshold	int	Minimum words per block
Content	only_text	bool	Text-only extraction
Content	process_iframes	bool	Include iframe content
Debug	verbose	bool	Detailed logging
Debug	log_console	bool	Browser console logs


Simple Crawling
This guide covers the basics of web crawling with Crawl4AI. You'll learn how to set up a crawler, make your first request, and understand the response.

Basic Usage
Set up a simple crawl using BrowserConfig and CrawlerRunConfig:

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def main():
    browser_config = BrowserConfig()  # Default browser configuration
    run_config = CrawlerRunConfig()   # Default crawl run configuration

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        print(result.markdown)  # Print clean markdown content

if __name__ == "__main__":
    asyncio.run(main())
Understanding the Response
The arun() method returns a CrawlResult object with several useful properties. Here's a quick overview (see CrawlResult for complete details):

result = await crawler.arun(
    url="https://example.com",
    config=CrawlerRunConfig(fit_markdown=True)
)

# Different content formats
print(result.html)         # Raw HTML
print(result.cleaned_html) # Cleaned HTML
print(result.markdown.raw_markdown) # Raw markdown from cleaned html
print(result.markdown.fit_markdown) # Most relevant content in markdown

# Check success status
print(result.success)      # True if crawl succeeded
print(result.status_code)  # HTTP status code (e.g., 200, 404)

# Access extracted media and links
print(result.media)        # Dictionary of found media (images, videos, audio)
print(result.links)        # Dictionary of internal and external links
Adding Basic Options
Customize your crawl using CrawlerRunConfig:

run_config = CrawlerRunConfig(
    word_count_threshold=10,        # Minimum words per content block
    exclude_external_links=True,    # Remove external links
    remove_overlay_elements=True,   # Remove popups/modals
    process_iframes=True           # Process iframe content
)

result = await crawler.arun(
    url="https://example.com",
    config=run_config
)
Handling Errors
Always check if the crawl was successful:

run_config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=run_config)

if not result.success:
    print(f"Crawl failed: {result.error_message}")
    print(f"Status code: {result.status_code}")
Logging and Debugging
Enable verbose logging in BrowserConfig:

browser_config = BrowserConfig(verbose=True)

async with AsyncWebCrawler(config=browser_config) as crawler:
    run_config = CrawlerRunConfig()
    result = await crawler.arun(url="https://example.com", config=run_config)
Complete Example
Here's a more comprehensive example demonstrating common usage patterns:

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        # Content filtering
        word_count_threshold=10,
        excluded_tags=['form', 'header'],
        exclude_external_links=True,

        # Content processing
        process_iframes=True,
        remove_overlay_elements=True,

        # Cache control
        cache_mode=CacheMode.ENABLED  # Use cache if available
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )

        if result.success:
            # Print clean content
            print("Content:", result.markdown[:500])  # First 500 chars

            # Process images
            for image in result.media["images"]:
                print(f"Found image: {image['src']}")

            # Process links
            for link in result.links["internal"]:
                print(f"Internal link: {link['href']}")

        else:
            print(f"Crawl failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())

    Crawl4AI CLI Guide
Table of Contents
Installation
Basic Usage
Configuration
Browser Configuration
Crawler Configuration
Extraction Configuration
Content Filtering
Advanced Features
LLM Q&A
Structured Data Extraction
Content Filtering
Output Formats
Examples
Configuration Reference
Best Practices & Tips
Basic Usage
The Crawl4AI CLI (crwl) provides a simple interface to the Crawl4AI library:

# Basic crawling
crwl https://example.com

# Get markdown output
crwl https://example.com -o markdown

# Verbose JSON output with cache bypass
crwl https://example.com -o json -v --bypass-cache

# See usage examples
crwl --example
Quick Example of Advanced Usage
If you clone the repository and run the following command, you will receive the content of the page in JSON format according to a JSON-CSS schema:

crwl "https://www.infoq.com/ai-ml-data-eng/" -e docs/examples/cli/extract_css.yml -s docs/examples/cli/css_schema.json -o json;
Configuration
Browser Configuration
Browser settings can be configured via YAML file or command line parameters:

# browser.yml
headless: true
viewport_width: 1280
user_agent_mode: "random"
verbose: true
ignore_https_errors: true
# Using config file
crwl https://example.com -B browser.yml

# Using direct parameters
crwl https://example.com -b "headless=true,viewport_width=1280,user_agent_mode=random"
Crawler Configuration
Control crawling behavior:

# crawler.yml
cache_mode: "bypass"
wait_until: "networkidle"
page_timeout: 30000
delay_before_return_html: 0.5
word_count_threshold: 100
scan_full_page: true
scroll_delay: 0.3
process_iframes: false
remove_overlay_elements: true
magic: true
verbose: true
# Using config file
crwl https://example.com -C crawler.yml

# Using direct parameters
crwl https://example.com -c "css_selector=#main,delay_before_return_html=2,scan_full_page=true"
Extraction Configuration
Two types of extraction are supported:

CSS/XPath-based extraction:
# extract_css.yml
type: "json-css"
params:
  verbose: true
// css_schema.json
{
  "name": "ArticleExtractor",
  "baseSelector": ".article",
  "fields": [
    {
      "name": "title",
      "selector": "h1.title",
      "type": "text"
    },
    {
      "name": "link",
      "selector": "a.read-more",
      "type": "attribute",
      "attribute": "href"
    }
  ]
}
LLM-based extraction:
# extract_llm.yml
type: "llm"
provider: "openai/gpt-4"
instruction: "Extract all articles with their titles and links"
api_token: "your-token"
params:
  temperature: 0.3
  max_tokens: 1000
// llm_schema.json
{
  "title": "Article",
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The title of the article"
    },
    "link": {
      "type": "string",
      "description": "URL to the full article"
    }
  }
}
Advanced Features
LLM Q&A
Ask questions about crawled content:

# Simple question
crwl https://example.com -q "What is the main topic discussed?"

# View content then ask questions
crwl https://example.com -o markdown  # See content first
crwl https://example.com -q "Summarize the key points"
crwl https://example.com -q "What are the conclusions?"

# Combined with advanced crawling
crwl https://example.com \
    -B browser.yml \
    -c "css_selector=article,scan_full_page=true" \
    -q "What are the pros and cons mentioned?"
First-time setup: - Prompts for LLM provider and API token - Saves configuration in ~/.crawl4ai/global.yml - Supports various providers (openai/gpt-4, anthropic/claude-3-sonnet, etc.) - For case of ollama you do not need to provide API token. - See LiteLLM Providers for full list

Structured Data Extraction
Extract structured data using CSS selectors:

crwl https://example.com \
    -e extract_css.yml \
    -s css_schema.json \
    -o json
Or using LLM-based extraction:

crwl https://example.com \
    -e extract_llm.yml \
    -s llm_schema.json \
    -o json
Content Filtering
Filter content for relevance:

# filter_bm25.yml
type: "bm25"
query: "target content"
threshold: 1.0

# filter_pruning.yml
type: "pruning"
query: "focus topic"
threshold: 0.48
crwl https://example.com -f filter_bm25.yml -o markdown-fit
Output Formats
all - Full crawl result including metadata
json - Extracted structured data (when using extraction)
markdown / md - Raw markdown output
markdown-fit / md-fit - Filtered markdown for better readability
Complete Examples
Basic Extraction:

crwl https://example.com \
    -B browser.yml \
    -C crawler.yml \
    -o json
Structured Data Extraction:

crwl https://example.com \
    -e extract_css.yml \
    -s css_schema.json \
    -o json \
    -v
LLM Extraction with Filtering:

crwl https://example.com \
    -B browser.yml \
    -e extract_llm.yml \
    -s llm_schema.json \
    -f filter_bm25.yml \
    -o json
Interactive Q&A:

# First crawl and view
crwl https://example.com -o markdown

# Then ask questions
crwl https://example.com -q "What are the main points?"
crwl https://example.com -q "Summarize the conclusions"