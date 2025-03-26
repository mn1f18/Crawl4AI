Getting Started with Crawl4AI
Welcome to Crawl4AI, an open-source LLM-friendly Web Crawler & Scraper. In this tutorial, you’ll:

Run your first crawl using minimal configuration.
Generate Markdown output (and learn how it’s influenced by content filters).
Experiment with a simple CSS-based extraction strategy.
See a glimpse of LLM-based extraction (including open-source and closed-source model options).
Crawl a dynamic page that loads content via JavaScript.
1. Introduction
Crawl4AI provides:

An asynchronous crawler, AsyncWebCrawler.
Configurable browser and run settings via BrowserConfig and CrawlerRunConfig.
Automatic HTML-to-Markdown conversion via DefaultMarkdownGenerator (supports optional filters).
Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).
By the end of this guide, you’ll have performed a basic crawl, generated Markdown, tried out two extraction strategies, and crawled a dynamic page that uses “Load More” buttons or JavaScript updates.

2. Your First Crawl
Here’s a minimal Python script that creates an AsyncWebCrawler, fetches a webpage, and prints the first 300 characters of its Markdown output:

import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])  # Print first 300 chars

if __name__ == "__main__":
    asyncio.run(main())
What’s happening? - AsyncWebCrawler launches a headless browser (Chromium by default). - It fetches https://example.com. - Crawl4AI automatically converts the HTML into Markdown.

You now have a simple, working crawl!

3. Basic Configuration (Light Introduction)
Crawl4AI’s crawler can be heavily customized using two main classes:

1. BrowserConfig: Controls browser behavior (headless or full UI, user agent, JavaScript toggles, etc.).
2. CrawlerRunConfig: Controls how each crawl runs (caching, extraction, timeouts, hooking, etc.).

Below is an example with minimal usage:

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_conf
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
IMPORTANT: By default cache mode is set to CacheMode.ENABLED. So to have fresh content, you need to set it to CacheMode.BYPASS

We’ll explore more advanced config in later tutorials (like enabling proxies, PDF output, multi-tab sessions, etc.). For now, just note how you pass these objects to manage crawling.

4. Generating Markdown Output
By default, Crawl4AI automatically generates Markdown from each crawled page. However, the exact output depends on whether you specify a markdown generator or content filter.

result.markdown:
The direct HTML-to-Markdown conversion.
result.markdown.fit_markdown:
The same content after applying any configured content filter (e.g., PruningContentFilter).
Example: Using a Filter with DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
)

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://news.ycombinator.com", config=config)
    print("Raw Markdown length:", len(result.markdown.raw_markdown))
    print("Fit Markdown length:", len(result.markdown.fit_markdown))
Note: If you do not specify a content filter or markdown generator, you’ll typically see only the raw Markdown. PruningContentFilter may adds around 50ms in processing time. We’ll dive deeper into these strategies in a dedicated Markdown Generation tutorial.

5. Simple Data Extraction (CSS-based)
Crawl4AI can also extract structured data (JSON) using CSS or XPath selectors. Below is a minimal CSS-based example:

New! Crawl4AI now provides a powerful utility to automatically generate extraction schemas using LLM. This is a one-time cost that gives you a reusable schema for fast, LLM-free extractions:

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai import LLMConfig

# Generate a schema (one-time cost)
html = "<div class='product'><h2>Gaming Laptop</h2><span class='price'>$999.99</span></div>"

# Using OpenAI (requires API token)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-openai-token")  # Required for OpenAI
)

# Or using Ollama (open source, no token needed)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_config = LLMConfig(provider="ollama/llama3.3", api_token=None)  # Not needed for Ollama
)

# Use the schema for fast, repeated extractions
strategy = JsonCssExtractionStrategy(schema)
For a complete guide on schema generation and advanced usage, see No-LLM Extraction Strategies.

Here's a basic extraction example:

import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    schema = {
        "name": "Example Items",
        "baseSelector": "div.item",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    raw_html = "<div class='item'><h2>Item 1</h2><a href='https://example.com/item1'>Link 1</a></div>"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw://" + raw_html,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema)
            )
        )
        # The JSON output is stored in 'extracted_content'
        data = json.loads(result.extracted_content)
        print(data)

if __name__ == "__main__":
    asyncio.run(main())
Why is this helpful? - Great for repetitive page structures (e.g., item listings, articles). - No AI usage or costs. - The crawler returns a JSON string you can parse or store.

Tips: You can pass raw HTML to the crawler instead of a URL. To do so, prefix the HTML with raw://.

6. Simple Data Extraction (LLM-based)
For more complex or irregular pages, a language model can parse text intelligently into a structure you define. Crawl4AI supports open-source or closed-source providers:

Open-Source Models (e.g., ollama/llama3.3, no_token)
OpenAI Models (e.g., openai/gpt-4, requires api_token)
Or any provider supported by the underlying library
Below is an example using open-source style (no token) and closed-source:

import os
import json
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(headless=True)

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=LLMExtractionStrategy(
            llm_config = LLMConfig(provider=provider,api_token=api_token),
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content.""",
            extra_args=extra_args,
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/", config=crawler_config
        )
        print(result.extracted_content)

if __name__ == "__main__":

    asyncio.run(
        extract_structured_data_using_llm(
            provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY")
        )
    )
What’s happening? - We define a Pydantic schema (PricingInfo) describing the fields we want. - The LLM extraction strategy uses that schema and your instructions to transform raw text into structured JSON. - Depending on the provider and api_token, you can use local models or a remote API.

7. Multi-URL Concurrency (Preview)
If you need to crawl multiple URLs in parallel, you can use arun_many(). By default, Crawl4AI employs a MemoryAdaptiveDispatcher, automatically adjusting concurrency based on system resources. Here’s a quick glimpse:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def quick_parallel_example():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]

    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True  # Enable streaming mode
    )

    async with AsyncWebCrawler() as crawler:
        # Stream results as they complete
        async for result in await crawler.arun_many(urls, config=run_conf):
            if result.success:
                print(f"[OK] {result.url}, length: {len(result.markdown.raw_markdown)}")
            else:
                print(f"[ERROR] {result.url} => {result.error_message}")

        # Or get all results at once (default behavior)
        run_conf = run_conf.clone(stream=False)
        results = await crawler.arun_many(urls, config=run_conf)
        for res in results:
            if res.success:
                print(f"[OK] {res.url}, length: {len(res.markdown.raw_markdown)}")
            else:
                print(f"[ERROR] {res.url} => {res.error_message}")

if __name__ == "__main__":
    asyncio.run(quick_parallel_example())
The example above shows two ways to handle multiple URLs: 1. Streaming mode (stream=True): Process results as they become available using async for 2. Batch mode (stream=False): Wait for all results to complete

For more advanced concurrency (e.g., a semaphore-based approach, adaptive memory usage throttling, or customized rate limiting), see Advanced Multi-URL Crawling.

8. Dynamic Content Example
Some sites require multiple “page clicks” or dynamic JavaScript updates. Below is an example showing how to click a “Next Page” button and wait for new commits to load on GitHub, using BrowserConfig and CrawlerRunConfig:

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "KidoCode Courses",
        "baseSelector": "section.charge-methodology .w-tab-content > div",
        "fields": [
            {
                "name": "section_title",
                "selector": "h3.heading-50",
                "type": "text",
            },
            {
                "name": "section_description",
                "selector": ".charge-content",
                "type": "text",
            },
            {
                "name": "course_name",
                "selector": ".text-block-93",
                "type": "text",
            },
            {
                "name": "course_description",
                "selector": ".course-content-text",
                "type": "text",
            },
            {
                "name": "course_icon",
                "selector": ".image-92",
                "type": "attribute",
                "attribute": "src",
            },
        ],
    }

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    js_click_tabs = """
    (async () => {
        const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");
        for(let tab of tabs) {
            tab.scrollIntoView();
            tab.click();
            await new Promise(r => setTimeout(r, 500));
        }
    })();
    """

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        js_code=[js_click_tabs],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology", config=crawler_config
        )

        companies = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(companies)} companies")
        print(json.dumps(companies[0], indent=2))

async def main():
    await extract_structured_data_using_css_extractor()

if __name__ == "__main__":
    asyncio.run(main())
Key Points:

BrowserConfig(headless=False): We want to watch it click “Next Page.”
CrawlerRunConfig(...): We specify the extraction strategy, pass session_id to reuse the same page.
js_code and wait_for are used for subsequent pages (page > 0) to click the “Next” button and wait for new commits to load.
js_only=True indicates we’re not re-navigating but continuing the existing session.
Finally, we call kill_session() to clean up the page and browser session.



imple Crawling
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


    Deep Crawling
One of Crawl4AI's most powerful features is its ability to perform configurable deep crawling that can explore websites beyond a single page. With fine-tuned control over crawl depth, domain boundaries, and content filtering, Crawl4AI gives you the tools to extract precisely the content you need.

In this tutorial, you'll learn:

How to set up a Basic Deep Crawler with BFS strategy
Understanding the difference between streamed and non-streamed output
Implementing filters and scorers to target specific content
Creating advanced filtering chains for sophisticated crawls
Using BestFirstCrawling for intelligent exploration prioritization
Prerequisites
- You’ve completed or read AsyncWebCrawler Basics to understand how to run a simple crawl.
- You know how to configure CrawlerRunConfig.

1. Quick Example
Here's a minimal code snippet that implements a basic deep crawl using the BFSDeepCrawlStrategy:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://example.com", config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
What's happening?
- BFSDeepCrawlStrategy(max_depth=2, include_external=False) instructs Crawl4AI to: - Crawl the starting page (depth 0) plus 2 more levels - Stay within the same domain (don't follow external links) - Each result contains metadata like the crawl depth - Results are returned as a list after all crawling is complete

2. Understanding Deep Crawling Strategy Options
2.1 BFSDeepCrawlStrategy (Breadth-First Search)
The BFSDeepCrawlStrategy uses a breadth-first approach, exploring all links at one depth before moving deeper:

from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

# Basic configuration
strategy = BFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=50,              # Maximum number of pages to crawl (optional)
    score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
)
Key parameters: - max_depth: Number of levels to crawl beyond the starting page - include_external: Whether to follow links to other domains - max_pages: Maximum number of pages to crawl (default: infinite) - score_threshold: Minimum score for URLs to be crawled (default: -inf) - filter_chain: FilterChain instance for URL filtering - url_scorer: Scorer instance for evaluating URLs

2.2 DFSDeepCrawlStrategy (Depth-First Search)
The DFSDeepCrawlStrategy uses a depth-first approach, explores as far down a branch as possible before backtracking.

from crawl4ai.deep_crawling import DFSDeepCrawlStrategy

# Basic configuration
strategy = DFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=30,              # Maximum number of pages to crawl (optional)
    score_threshold=0.5,       # Minimum score for URLs to be crawled (optional)
)
Key parameters: - max_depth: Number of levels to crawl beyond the starting page - include_external: Whether to follow links to other domains - max_pages: Maximum number of pages to crawl (default: infinite) - score_threshold: Minimum score for URLs to be crawled (default: -inf) - filter_chain: FilterChain instance for URL filtering - url_scorer: Scorer instance for evaluating URLs

2.3 BestFirstCrawlingStrategy (⭐️ - Recommended Deep crawl strategy)
For more intelligent crawling, use BestFirstCrawlingStrategy with scorers to prioritize the most relevant pages:

from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

# Create a scorer
scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7
)

# Configure the strategy
strategy = BestFirstCrawlingStrategy(
    max_depth=2,
    include_external=False,
    url_scorer=scorer,
    max_pages=25,              # Maximum number of pages to crawl (optional)
)
This crawling approach: - Evaluates each discovered URL based on scorer criteria - Visits higher-scoring pages first - Helps focus crawl resources on the most relevant content - Can limit total pages crawled with max_pages - Does not need score_threshold as it naturally prioritizes by score

3. Streaming vs. Non-Streaming Results
Crawl4AI can return results in two modes:

3.1 Non-Streaming Mode (Default)
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=False  # Default behavior
)

async with AsyncWebCrawler() as crawler:
    # Wait for ALL results to be collected before returning
    results = await crawler.arun("https://example.com", config=config)

    for result in results:
        process_result(result)
When to use non-streaming mode: - You need the complete dataset before processing - You're performing batch operations on all results together - Crawl time isn't a critical factor

3.2 Streaming Mode
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=True  # Enable streaming
)

async with AsyncWebCrawler() as crawler:
    # Returns an async iterator
    async for result in await crawler.arun("https://example.com", config=config):
        # Process each result as it becomes available
        process_result(result)
Benefits of streaming mode: - Process results immediately as they're discovered - Start working with early results while crawling continues - Better for real-time applications or progressive display - Reduces memory pressure when handling many pages

4. Filtering Content with Filter Chains
Filters help you narrow down which pages to crawl. Combine multiple filters using FilterChain for powerful targeting.

4.1 Basic URL Pattern Filter
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

# Only follow URLs containing "blog" or "docs"
url_filter = URLPatternFilter(patterns=["*blog*", "*docs*"])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([url_filter])
    )
)
4.2 Combining Multiple Filters
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter
)

# Create a chain of filters
filter_chain = FilterChain([
    # Only follow URLs with specific patterns
    URLPatternFilter(patterns=["*guide*", "*tutorial*"]),

    # Only crawl specific domains
    DomainFilter(
        allowed_domains=["docs.example.com"],
        blocked_domains=["old.docs.example.com"]
    ),

    # Only include specific content types
    ContentTypeFilter(allowed_types=["text/html"])
])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2,
        filter_chain=filter_chain
    )
)
4.3 Available Filter Types
Crawl4AI includes several specialized filters:

URLPatternFilter: Matches URL patterns using wildcard syntax
DomainFilter: Controls which domains to include or exclude
ContentTypeFilter: Filters based on HTTP Content-Type
ContentRelevanceFilter: Uses similarity to a text query
SEOFilter: Evaluates SEO elements (meta tags, headers, etc.)
5. Using Scorers for Prioritized Crawling
Scorers assign priority values to discovered URLs, helping the crawler focus on the most relevant content first.

5.1 KeywordRelevanceScorer
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

# Create a keyword relevance scorer
keyword_scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7  # Importance of this scorer (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BestFirstCrawlingStrategy(
        max_depth=2,
        url_scorer=keyword_scorer
    ),
    stream=True  # Recommended with BestFirstCrawling
)

# Results will come in order of relevance score
async with AsyncWebCrawler() as crawler:
    async for result in await crawler.arun("https://example.com", config=config):
        score = result.metadata.get("score", 0)
        print(f"Score: {score:.2f} | {result.url}")
How scorers work: - Evaluate each discovered URL before crawling - Calculate relevance based on various signals - Help the crawler make intelligent choices about traversal order

6. Advanced Filtering Techniques
6.1 SEO Filter for Quality Assessment
The SEOFilter helps you identify pages with strong SEO characteristics:

from crawl4ai.deep_crawling.filters import FilterChain, SEOFilter

# Create an SEO filter that looks for specific keywords in page metadata
seo_filter = SEOFilter(
    threshold=0.5,  # Minimum score (0.0 to 1.0)
    keywords=["tutorial", "guide", "documentation"]
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([seo_filter])
    )
)
6.2 Content Relevance Filter
The ContentRelevanceFilter analyzes the actual content of pages:

from crawl4ai.deep_crawling.filters import FilterChain, ContentRelevanceFilter

# Create a content relevance filter
relevance_filter = ContentRelevanceFilter(
    query="Web crawling and data extraction with Python",
    threshold=0.7  # Minimum similarity score (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([relevance_filter])
    )
)
This filter: - Measures semantic similarity between query and page content - It's a BM25-based relevance filter using head section content

7. Building a Complete Advanced Crawler
This example combines multiple techniques for a sophisticated crawl:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

async def run_advanced_crawler():
    # Create a sophisticated filter chain
    filter_chain = FilterChain([
        # Domain boundaries
        DomainFilter(
            allowed_domains=["docs.example.com"],
            blocked_domains=["old.docs.example.com"]
        ),

        # URL patterns to include
        URLPatternFilter(patterns=["*guide*", "*tutorial*", "*blog*"]),

        # Content type filtering
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    # Create a relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    # Set up the configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    # Execute the crawl
    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.example.com", config=config):
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")

    # Analyze the results
    print(f"Crawled {len(results)} high-value pages")
    print(f"Average score: {sum(r.metadata.get('score', 0) for r in results) / len(results):.2f}")

    # Group by depth
    depth_counts = {}
    for result in results:
        depth = result.metadata.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    print("Pages crawled by depth:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Depth {depth}: {count} pages")

if __name__ == "__main__":
    asyncio.run(run_advanced_crawler())
8. Limiting and Controlling Crawl Size
8.1 Using max_pages
You can limit the total number of pages crawled with the max_pages parameter:

# Limit to exactly 20 pages regardless of depth
strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=20
)
This feature is useful for: - Controlling API costs - Setting predictable execution times - Focusing on the most important content - Testing crawl configurations before full execution

8.2 Using score_threshold
For BFS and DFS strategies, you can set a minimum score threshold to only crawl high-quality pages:

# Only follow links with scores above 0.4
strategy = DFSDeepCrawlStrategy(
    max_depth=2,
    url_scorer=KeywordRelevanceScorer(keywords=["api", "guide", "reference"]),
    score_threshold=0.4  # Skip URLs with scores below this value
)
Note that for BestFirstCrawlingStrategy, score_threshold is not needed since pages are already processed in order of highest score first.

9. Common Pitfalls & Tips
1.Set realistic limits. Be cautious with max_depth values > 3, which can exponentially increase crawl size. Use max_pages to set hard limits.

2.Don't neglect the scoring component. BestFirstCrawling works best with well-tuned scorers. Experiment with keyword weights for optimal prioritization.

3.Be a good web citizen. Respect robots.txt. (disabled by default)

4.Handle page errors gracefully. Not all pages will be accessible. Check result.status when processing results.

5.Balance breadth vs. depth. Choose your strategy wisely - BFS for comprehensive coverage, DFS for deep exploration, BestFirst for focused relevance-based crawling.


Crawl Result and Output
When you call arun() on a page, Crawl4AI returns a CrawlResult object containing everything you might need—raw HTML, a cleaned version, optional screenshots or PDFs, structured extraction results, and more. This document explains those fields and how they map to different output types.

1. The CrawlResult Model
Below is the core schema. Each field captures a different aspect of the crawl’s result:

class MarkdownGenerationResult(BaseModel):
    raw_markdown: str
    markdown_with_citations: str
    references_markdown: str
    fit_markdown: Optional[str] = None
    fit_html: Optional[str] = None

class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    screenshot: Optional[str] = None
    pdf : Optional[bytes] = None
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    class Config:
        arbitrary_types_allowed = True
Table: Key Fields in CrawlResult
Field (Name & Type)	Description
url (str)	The final or actual URL crawled (in case of redirects).
html (str)	Original, unmodified page HTML. Good for debugging or custom processing.
success (bool)	True if the crawl completed without major errors, else False.
cleaned_html (Optional[str])	Sanitized HTML with scripts/styles removed; can exclude tags if configured via excluded_tags etc.
media (Dict[str, List[Dict]])	Extracted media info (images, audio, etc.), each with attributes like src, alt, score, etc.
links (Dict[str, List[Dict]])	Extracted link data, split by internal and external. Each link usually has href, text, etc.
downloaded_files (Optional[List[str]])	If accept_downloads=True in BrowserConfig, this lists the filepaths of saved downloads.
screenshot (Optional[str])	Screenshot of the page (base64-encoded) if screenshot=True.
pdf (Optional[bytes])	PDF of the page if pdf=True.
markdown (Optional[str or MarkdownGenerationResult])	It holds a MarkdownGenerationResult. Over time, this will be consolidated into markdown. The generator can provide raw markdown, citations, references, and optionally fit_markdown.
extracted_content (Optional[str])	The output of a structured extraction (CSS/LLM-based) stored as JSON string or other text.
metadata (Optional[dict])	Additional info about the crawl or extracted data.
error_message (Optional[str])	If success=False, contains a short description of what went wrong.
session_id (Optional[str])	The ID of the session used for multi-page or persistent crawling.
response_headers (Optional[dict])	HTTP response headers, if captured.
status_code (Optional[int])	HTTP status code (e.g., 200 for OK).
ssl_certificate (Optional[SSLCertificate])	SSL certificate info if fetch_ssl_certificate=True.
2. HTML Variants
html: Raw HTML
Crawl4AI preserves the exact HTML as result.html. Useful for:

Debugging page issues or checking the original content.
Performing your own specialized parse if needed.
cleaned_html: Sanitized
If you specify any cleanup or exclusion parameters in CrawlerRunConfig (like excluded_tags, remove_forms, etc.), you’ll see the result here:

config = CrawlerRunConfig(
    excluded_tags=["form", "header", "footer"],
    keep_data_attributes=False
)
result = await crawler.arun("https://example.com", config=config)
print(result.cleaned_html)  # Freed of forms, header, footer, data-* attributes
3. Markdown Generation
3.1 markdown
markdown: The current location for detailed markdown output, returning a MarkdownGenerationResult object.
markdown_v2: Deprecated since v0.5.
MarkdownGenerationResult Fields:

Field	Description
raw_markdown	The basic HTML→Markdown conversion.
markdown_with_citations	Markdown including inline citations that reference links at the end.
references_markdown	The references/citations themselves (if citations=True).
fit_markdown	The filtered/“fit” markdown if a content filter was used.
fit_html	The filtered HTML that generated fit_markdown.
3.2 Basic Example with a Markdown Generator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        options={"citations": True, "body_width": 80}  # e.g. pass html2text style options
    )
)
result = await crawler.arun(url="https://example.com", config=config)

md_res = result.markdown  # or eventually 'result.markdown'
print(md_res.raw_markdown[:500])
print(md_res.markdown_with_citations)
print(md_res.references_markdown)
Note: If you use a filter like PruningContentFilter, you’ll get fit_markdown and fit_html as well.

4. Structured Extraction: extracted_content
If you run a JSON-based extraction strategy (CSS, XPath, LLM, etc.), the structured data is not stored in markdown—it’s placed in result.extracted_content as a JSON string (or sometimes plain text).

Example: CSS Extraction with raw:// HTML
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    schema = {
        "name": "Example Items",
        "baseSelector": "div.item",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }
    raw_html = "<div class='item'><h2>Item 1</h2><a href='https://example.com/item1'>Link 1</a></div>"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw://" + raw_html,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema)
            )
        )
        data = json.loads(result.extracted_content)
        print(data)

if __name__ == "__main__":
    asyncio.run(main())
Here: - url="raw://..." passes the HTML content directly, no network requests.
- The CSS extraction strategy populates result.extracted_content with the JSON array [{"title": "...", "link": "..."}].

5. More Fields: Links, Media, and More
5.1 links
A dictionary, typically with "internal" and "external" lists. Each entry might have href, text, title, etc. This is automatically captured if you haven’t disabled link extraction.

print(result.links["internal"][:3])  # Show first 3 internal links
5.2 media
Similarly, a dictionary with "images", "audio", "video", etc. Each item could include src, alt, score, and more, if your crawler is set to gather them.

images = result.media.get("images", [])
for img in images:
    print("Image URL:", img["src"], "Alt:", img.get("alt"))
5.3 screenshot and pdf
If you set screenshot=True or pdf=True in CrawlerRunConfig, then:

result.screenshot contains a base64-encoded PNG string.
result.pdf contains raw PDF bytes (you can write them to a file).
with open("page.pdf", "wb") as f:
    f.write(result.pdf)
5.4 ssl_certificate
If fetch_ssl_certificate=True, result.ssl_certificate holds details about the site’s SSL cert, such as issuer, validity dates, etc.

6. Accessing These Fields
After you run:

result = await crawler.arun(url="https://example.com", config=some_config)
Check any field:

if result.success:
    print(result.status_code, result.response_headers)
    print("Links found:", len(result.links.get("internal", [])))
    if result.markdown:
        print("Markdown snippet:", result.markdown.raw_markdown[:200])
    if result.extracted_content:
        print("Structured JSON:", result.extracted_content)
else:
    print("Error:", result.error_message)
Deprecation: Since v0.5 result.markdown_v2, result.fit_html,result.fit_markdown are deprecated. Use result.markdown instead! It holds MarkdownGenerationResult, which includes fit_html and fit_markdown as it's properties.

Browser, Crawler & LLM Configuration (Quick Overview)
Crawl4AI’s flexibility stems from two key classes:

1. BrowserConfig – Dictates how the browser is launched and behaves (e.g., headless or visible, proxy, user agent).
2. CrawlerRunConfig – Dictates how each crawl operates (e.g., caching, extraction, timeouts, JavaScript code to run, etc.).
3. LLMConfig - Dictates how LLM providers are configured. (model, api token, base url, temperature etc.)

In most examples, you create one BrowserConfig for the entire crawler session, then pass a fresh or re-used CrawlerRunConfig whenever you call arun(). This tutorial shows the most commonly used parameters. If you need advanced or rarely used fields, see the Configuration Parameters.

1. BrowserConfig Essentials
class BrowserConfig:
    def __init__(
        browser_type="chromium",
        headless=True,
        proxy_config=None,
        viewport_width=1080,
        viewport_height=600,
        verbose=True,
        use_persistent_context=False,
        user_data_dir=None,
        cookies=None,
        headers=None,
        user_agent=None,
        text_mode=False,
        light_mode=False,
        extra_args=None,
        # ... other advanced parameters omitted here
    ):
        ...
Key Fields to Note
1. browser_type
- Options: "chromium", "firefox", or "webkit".
- Defaults to "chromium".
- If you need a different engine, specify it here.

2. headless
- True: Runs the browser in headless mode (invisible browser).
- False: Runs the browser in visible mode, which helps with debugging.

3. proxy_config
- A dictionary with fields like:

{
    "server": "http://proxy.example.com:8080", 
    "username": "...", 
    "password": "..."
}
- Leave as None if a proxy is not required.
4. viewport_width & viewport_height:
- The initial window size.
- Some sites behave differently with smaller or bigger viewports.

5. verbose:
- If True, prints extra logs.
- Handy for debugging.

6. use_persistent_context:
- If True, uses a persistent browser profile, storing cookies/local storage across runs.
- Typically also set user_data_dir to point to a folder.

7. cookies & headers:
- If you want to start with specific cookies or add universal HTTP headers, set them here.
- E.g. cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}].

8. user_agent:
- Custom User-Agent string. If None, a default is used.
- You can also set user_agent_mode="random" for randomization (if you want to fight bot detection).

9. text_mode & light_mode:
- text_mode=True disables images, possibly speeding up text-only crawls.
- light_mode=True turns off certain background features for performance.

10. extra_args:
- Additional flags for the underlying browser.
- E.g. ["--disable-extensions"].

Helper Methods
Both configuration classes provide a clone() method to create modified copies:

# Create a base browser config
base_browser = BrowserConfig(
    browser_type="chromium",
    headless=True,
    text_mode=True
)

# Create a visible browser config for debugging
debug_browser = base_browser.clone(
    headless=False,
    verbose=True
)
Minimal Example:

from crawl4ai import AsyncWebCrawler, BrowserConfig

browser_conf = BrowserConfig(
    browser_type="firefox",
    headless=False,
    text_mode=True
)

async with AsyncWebCrawler(config=browser_conf) as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown[:300])
2. CrawlerRunConfig Essentials
class CrawlerRunConfig:
    def __init__(
        word_count_threshold=200,
        extraction_strategy=None,
        markdown_generator=None,
        cache_mode=None,
        js_code=None,
        wait_for=None,
        screenshot=False,
        pdf=False,
        enable_rate_limiting=False,
        rate_limit_config=None,
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=20,
        display_mode=None,
        verbose=True,
        stream=False,  # Enable streaming for arun_many()
        # ... other advanced parameters omitted
    ):
        ...
Key Fields to Note
1. word_count_threshold:
- The minimum word count before a block is considered.
- If your site has lots of short paragraphs or items, you can lower it.

2. extraction_strategy:
- Where you plug in JSON-based extraction (CSS, LLM, etc.).
- If None, no structured extraction is done (only raw/cleaned HTML + markdown).

3. markdown_generator:
- E.g., DefaultMarkdownGenerator(...), controlling how HTML→Markdown conversion is done.
- If None, a default approach is used.

4. cache_mode:
- Controls caching behavior (ENABLED, BYPASS, DISABLED, etc.).
- If None, defaults to some level of caching or you can specify CacheMode.ENABLED.

5. js_code:
- A string or list of JS strings to execute.
- Great for “Load More” buttons or user interactions.

6. wait_for:
- A CSS or JS expression to wait for before extracting content.
- Common usage: wait_for="css:.main-loaded" or wait_for="js:() => window.loaded === true".

7. screenshot & pdf:
- If True, captures a screenshot or PDF after the page is fully loaded.
- The results go to result.screenshot (base64) or result.pdf (bytes).

8. verbose:
- Logs additional runtime details.
- Overlaps with the browser’s verbosity if also set to True in BrowserConfig.

9. enable_rate_limiting:
- If True, enables rate limiting for batch processing.
- Requires rate_limit_config to be set.

10. memory_threshold_percent:
- The memory threshold (as a percentage) to monitor.
- If exceeded, the crawler will pause or slow down.

11. check_interval:
- The interval (in seconds) to check system resources.
- Affects how often memory and CPU usage are monitored.

12. max_session_permit:
- The maximum number of concurrent crawl sessions.
- Helps prevent overwhelming the system.

13. display_mode:
- The display mode for progress information (DETAILED, BRIEF, etc.).
- Affects how much information is printed during the crawl.

Helper Methods
The clone() method is particularly useful for creating variations of your crawler configuration:

# Create a base configuration
base_config = CrawlerRunConfig(
    cache_mode=CacheMode.ENABLED,
    word_count_threshold=200,
    wait_until="networkidle"
)

# Create variations for different use cases
stream_config = base_config.clone(
    stream=True,  # Enable streaming mode
    cache_mode=CacheMode.BYPASS
)

debug_config = base_config.clone(
    page_timeout=120000,  # Longer timeout for debugging
    verbose=True
)
The clone() method: - Creates a new instance with all the same settings - Updates only the specified parameters - Leaves the original configuration unchanged - Perfect for creating variations without repeating all parameters

3. LLMConfig Essentials
Key fields to note
1. provider:
- Which LLM provoder to use. - Possible values are "ollama/llama3","groq/llama3-70b-8192","groq/llama3-8b-8192", "openai/gpt-4o-mini" ,"openai/gpt-4o","openai/o1-mini","openai/o1-preview","openai/o3-mini","openai/o3-mini-high","anthropic/claude-3-haiku-20240307","anthropic/claude-3-opus-20240229","anthropic/claude-3-sonnet-20240229","anthropic/claude-3-5-sonnet-20240620","gemini/gemini-pro","gemini/gemini-1.5-pro","gemini/gemini-2.0-flash","gemini/gemini-2.0-flash-exp","gemini/gemini-2.0-flash-lite-preview-02-05","deepseek/deepseek-chat"
(default: "openai/gpt-4o-mini")

2. api_token:
- Optional. When not provided explicitly, api_token will be read from environment variables based on provider. For example: If a gemini model is passed as provider then,"GEMINI_API_KEY" will be read from environment variables
- API token of LLM provider
eg: api_token = "gsk_1ClHGGJ7Lpn4WGybR7vNWGdyb3FY7zXEw3SCiy0BAVM9lL8CQv" - Environment variable - use with prefix "env:"
eg:api_token = "env: GROQ_API_KEY"

3. base_url:
- If your provider has a custom endpoint

llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
4. Putting It All Together
In a typical scenario, you define one BrowserConfig for your crawler session, then create one or more CrawlerRunConfig & LLMConfig depending on each call’s needs:

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # 1) Browser config: headless, bigger viewport, no proxy
    browser_conf = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720
    )

    # 2) Example extraction strategy
    schema = {
        "name": "Articles",
        "baseSelector": "div.article",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }
    extraction = JsonCssExtractionStrategy(schema)

    # 3) Example LLM content filtering

    gemini_config = LLMConfig(
        provider="gemini/gemini-1.5-pro" 
        api_token = "env:GEMINI_API_TOKEN"
    )

    # Initialize LLM filter with specific instruction
    filter = LLMContentFilter(
        llm_config=gemini_config,  # or your preferred provider
        instruction="""
        Focus on extracting the core educational content.
        Include:
        - Key concepts and explanations
        - Important code examples
        - Essential technical details
        Exclude:
        - Navigation elements
        - Sidebars
        - Footer content
        Format the output as clean markdown with proper code blocks and headers.
        """,
        chunk_token_threshold=500,  # Adjust based on your needs
        verbose=True
    )

    md_generator = DefaultMarkdownGenerator(
    content_filter=filter,
    options={"ignore_links": True}

    # 4) Crawler run config: skip cache, use extraction
    run_conf = CrawlerRunConfig(
        markdown_generator=md_generator,
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        # 4) Execute the crawl
        result = await crawler.arun(url="https://example.com/news", config=run_conf)

        if result.success:
            print("Extracted content:", result.extracted_content)
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
5. Next Steps
For a detailed list of available parameters (including advanced ones), see:

BrowserConfig, CrawlerRunConfig & LLMConfig Reference
You can explore topics like:

Custom Hooks & Auth (Inject JavaScript or handle login forms).
Session Management (Re-use pages, preserve state across multiple calls).
Magic Mode or Identity-based Crawling (Fight bot detection by simulating user behavior).
Advanced Caching (Fine-tune read/write cache modes).
6. Conclusion
BrowserConfig, CrawlerRunConfig and LLMConfig give you straightforward ways to define:

Which browser to launch, how it should run, and any proxy or user agent needs.
How each crawl should behave—caching, timeouts, JavaScript code, extraction strategies, etc.
Which LLM provider to use, api token, temperature and base url for custom endpoints

Markdown Generation Basics
One of Crawl4AI’s core features is generating clean, structured markdown from web pages. Originally built to solve the problem of extracting only the “actual” content and discarding boilerplate or noise, Crawl4AI’s markdown system remains one of its biggest draws for AI workflows.

In this tutorial, you’ll learn:

How to configure the Default Markdown Generator
How content filters (BM25 or Pruning) help you refine markdown and discard junk
The difference between raw markdown (result.markdown) and filtered markdown (fit_markdown)
Prerequisites
- You’ve completed or read AsyncWebCrawler Basics to understand how to run a simple crawl.
- You know how to configure CrawlerRunConfig.

1. Quick Example
Here’s a minimal code snippet that uses the DefaultMarkdownGenerator with no additional filtering:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)

        if result.success:
            print("Raw Markdown Output:\n")
            print(result.markdown)  # The unfiltered markdown from the page
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
What’s happening?
- CrawlerRunConfig( markdown_generator = DefaultMarkdownGenerator() ) instructs Crawl4AI to convert the final HTML into markdown at the end of each crawl.
- The resulting markdown is accessible via result.markdown.

2. How Markdown Generation Works
2.1 HTML-to-Text Conversion (Forked & Modified)
Under the hood, DefaultMarkdownGenerator uses a specialized HTML-to-text approach that:

Preserves headings, code blocks, bullet points, etc.
Removes extraneous tags (scripts, styles) that don’t add meaningful content.
Can optionally generate references for links or skip them altogether.
A set of options (passed as a dict) allows you to customize precisely how HTML converts to markdown. These map to standard html2text-like configuration plus your own enhancements (e.g., ignoring internal links, preserving certain tags verbatim, or adjusting line widths).

2.2 Link Citations & References
By default, the generator can convert <a href="..."> elements into [text][1] citations, then place the actual links at the bottom of the document. This is handy for research workflows that demand references in a structured manner.

2.3 Optional Content Filters
Before or after the HTML-to-Markdown step, you can apply a content filter (like BM25 or Pruning) to reduce noise and produce a “fit_markdown”—a heavily pruned version focusing on the page’s main text. We’ll cover these filters shortly.

3. Configuring the Default Markdown Generator
You can tweak the output by passing an options dict to DefaultMarkdownGenerator. For example:

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Example: ignore all links, don't escape HTML, and wrap text at 80 characters
    md_generator = DefaultMarkdownGenerator(
        options={
            "ignore_links": True,
            "escape_html": False,
            "body_width": 80
        }
    )

    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/docs", config=config)
        if result.success:
            print("Markdown:\n", result.markdown[:500])  # Just a snippet
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
Some commonly used options:

ignore_links (bool): Whether to remove all hyperlinks in the final markdown.
ignore_images (bool): Remove all ![image]() references.
escape_html (bool): Turn HTML entities into text (default is often True).
body_width (int): Wrap text at N characters. 0 or None means no wrapping.
skip_internal_links (bool): If True, omit #localAnchors or internal links referencing the same page.
include_sup_sub (bool): Attempt to handle <sup> / <sub> in a more readable way.
4. Content Filters
Content filters selectively remove or rank sections of text before turning them into Markdown. This is especially helpful if your page has ads, nav bars, or other clutter you don’t want.

4.1 BM25ContentFilter
If you have a search query, BM25 is a good choice:

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai import CrawlerRunConfig

bm25_filter = BM25ContentFilter(
    user_query="machine learning",
    bm25_threshold=1.2,
    use_stemming=True
)

md_generator = DefaultMarkdownGenerator(
    content_filter=bm25_filter,
    options={"ignore_links": True}
)

config = CrawlerRunConfig(markdown_generator=md_generator)
user_query: The term you want to focus on. BM25 tries to keep only content blocks relevant to that query.
bm25_threshold: Raise it to keep fewer blocks; lower it to keep more.
use_stemming: If True, variations of words match (e.g., “learn,” “learning,” “learnt”).
No query provided? BM25 tries to glean a context from page metadata, or you can simply treat it as a scorched-earth approach that discards text with low generic score. Realistically, you want to supply a query for best results.

4.2 PruningContentFilter
If you don’t have a specific query, or if you just want a robust “junk remover,” use PruningContentFilter. It analyzes text density, link density, HTML structure, and known patterns (like “nav,” “footer”) to systematically prune extraneous or repetitive sections.

from crawl4ai.content_filter_strategy import PruningContentFilter

prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",  # or "dynamic"
    min_word_threshold=50
)
threshold: Score boundary. Blocks below this score get removed.
threshold_type:
"fixed": Straight comparison (score >= threshold keeps the block).
"dynamic": The filter adjusts threshold in a data-driven manner.
min_word_threshold: Discard blocks under N words as likely too short or unhelpful.
When to Use PruningContentFilter
- You want a broad cleanup without a user query.
- The page has lots of repeated sidebars, footers, or disclaimers that hamper text extraction.

4.3 LLMContentFilter
For intelligent content filtering and high-quality markdown generation, you can use the LLMContentFilter. This filter leverages LLMs to generate relevant markdown while preserving the original content's meaning and structure:

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.content_filter_strategy import LLMContentFilter

async def main():
    # Initialize LLM filter with specific instruction
    filter = LLMContentFilter(
        llm_config = LLMConfig(provider="openai/gpt-4o",api_token="your-api-token"), #or use environment variable
        instruction="""
        Focus on extracting the core educational content.
        Include:
        - Key concepts and explanations
        - Important code examples
        - Essential technical details
        Exclude:
        - Navigation elements
        - Sidebars
        - Footer content
        Format the output as clean markdown with proper code blocks and headers.
        """,
        chunk_token_threshold=4096,  # Adjust based on your needs
        verbose=True
    )

    config = CrawlerRunConfig(
        content_filter=filter
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        print(result.markdown.fit_markdown)  # Filtered markdown content
Key Features: - Intelligent Filtering: Uses LLMs to understand and extract relevant content while maintaining context - Customizable Instructions: Tailor the filtering process with specific instructions - Chunk Processing: Handles large documents by processing them in chunks (controlled by chunk_token_threshold) - Parallel Processing: For better performance, use smaller chunk_token_threshold (e.g., 2048 or 4096) to enable parallel processing of content chunks

Two Common Use Cases:

Exact Content Preservation:

filter = LLMContentFilter(
    instruction="""
    Extract the main educational content while preserving its original wording and substance completely.
    1. Maintain the exact language and terminology
    2. Keep all technical explanations and examples intact
    3. Preserve the original flow and structure
    4. Remove only clearly irrelevant elements like navigation menus and ads
    """,
    chunk_token_threshold=4096
)
Focused Content Extraction:

filter = LLMContentFilter(
    instruction="""
    Focus on extracting specific types of content:
    - Technical documentation
    - Code examples
    - API references
    Reformat the content into clear, well-structured markdown
    """,
    chunk_token_threshold=4096
)
Performance Tip: Set a smaller chunk_token_threshold (e.g., 2048 or 4096) to enable parallel processing of content chunks. The default value is infinity, which processes the entire content as a single chunk.

5. Using Fit Markdown
When a content filter is active, the library produces two forms of markdown inside result.markdown:

1. raw_markdown: The full unfiltered markdown.
2. fit_markdown: A “fit” version where the filter has removed or trimmed noisy segments.

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.6),
            options={"ignore_links": True}
        )
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://news.example.com/tech", config=config)
        if result.success:
            print("Raw markdown:\n", result.markdown)

            # If a filter is used, we also have .fit_markdown:
            md_object = result.markdown  # or your equivalent
            print("Filtered markdown:\n", md_object.fit_markdown)
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
6. The MarkdownGenerationResult Object
If your library stores detailed markdown output in an object like MarkdownGenerationResult, you’ll see fields such as:

raw_markdown: The direct HTML-to-markdown transformation (no filtering).
markdown_with_citations: A version that moves links to reference-style footnotes.
references_markdown: A separate string or section containing the gathered references.
fit_markdown: The filtered markdown if you used a content filter.
fit_html: The corresponding HTML snippet used to generate fit_markdown (helpful for debugging or advanced usage).
Example:

md_obj = result.markdown  # your library’s naming may vary
print("RAW:\n", md_obj.raw_markdown)
print("CITED:\n", md_obj.markdown_with_citations)
print("REFERENCES:\n", md_obj.references_markdown)
print("FIT:\n", md_obj.fit_markdown)
Why Does This Matter?
- You can supply raw_markdown to an LLM if you want the entire text.
- Or feed fit_markdown into a vector database to reduce token usage.
- references_markdown can help you keep track of link provenance.

Below is a revised section under “Combining Filters (BM25 + Pruning)” that demonstrates how you can run two passes of content filtering without re-crawling, by taking the HTML (or text) from a first pass and feeding it into the second filter. It uses real code patterns from the snippet you provided for BM25ContentFilter, which directly accepts HTML strings (and can also handle plain text with minimal adaptation).

7. Combining Filters (BM25 + Pruning) in Two Passes
You might want to prune out noisy boilerplate first (with PruningContentFilter), and then rank what’s left against a user query (with BM25ContentFilter). You don’t have to crawl the page twice. Instead:

1. First pass: Apply PruningContentFilter directly to the raw HTML from result.html (the crawler’s downloaded HTML).
2. Second pass: Take the pruned HTML (or text) from step 1, and feed it into BM25ContentFilter, focusing on a user query.

Two-Pass Example
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from bs4 import BeautifulSoup

async def main():
    # 1. Crawl with minimal or no markdown generator, just get raw HTML
    config = CrawlerRunConfig(
        # If you only want raw HTML, you can skip passing a markdown_generator
        # or provide one but focus on .html in this example
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com/tech-article", config=config)

        if not result.success or not result.html:
            print("Crawl failed or no HTML content.")
            return

        raw_html = result.html

        # 2. First pass: PruningContentFilter on raw HTML
        pruning_filter = PruningContentFilter(threshold=0.5, min_word_threshold=50)

        # filter_content returns a list of "text chunks" or cleaned HTML sections
        pruned_chunks = pruning_filter.filter_content(raw_html)
        # This list is basically pruned content blocks, presumably in HTML or text form

        # For demonstration, let's combine these chunks back into a single HTML-like string
        # or you could do further processing. It's up to your pipeline design.
        pruned_html = "\n".join(pruned_chunks)

        # 3. Second pass: BM25ContentFilter with a user query
        bm25_filter = BM25ContentFilter(
            user_query="machine learning",
            bm25_threshold=1.2,
            language="english"
        )

        # returns a list of text chunks
        bm25_chunks = bm25_filter.filter_content(pruned_html)  

        if not bm25_chunks:
            print("Nothing matched the BM25 query after pruning.")
            return

        # 4. Combine or display final results
        final_text = "\n---\n".join(bm25_chunks)

        print("==== PRUNED OUTPUT (first pass) ====")
        print(pruned_html[:500], "... (truncated)")  # preview

        print("\n==== BM25 OUTPUT (second pass) ====")
        print(final_text[:500], "... (truncated)")

if __name__ == "__main__":
    asyncio.run(main())
What’s Happening?
1. Raw HTML: We crawl once and store the raw HTML in result.html.
2. PruningContentFilter: Takes HTML + optional parameters. It extracts blocks of text or partial HTML, removing headings/sections deemed “noise.” It returns a list of text chunks.
3. Combine or Transform: We join these pruned chunks back into a single HTML-like string. (Alternatively, you could store them in a list for further logic—whatever suits your pipeline.)
4. BM25ContentFilter: We feed the pruned string into BM25ContentFilter with a user query. This second pass further narrows the content to chunks relevant to “machine learning.”

No Re-Crawling: We used raw_html from the first pass, so there’s no need to run arun() again—no second network request.

Tips & Variations
Plain Text vs. HTML: If your pruned output is mostly text, BM25 can still handle it; just keep in mind it expects a valid string input. If you supply partial HTML (like "<p>some text</p>"), it will parse it as HTML.
Chaining in a Single Pipeline: If your code supports it, you can chain multiple filters automatically. Otherwise, manual two-pass filtering (as shown) is straightforward.
Adjust Thresholds: If you see too much or too little text in step one, tweak threshold=0.5 or min_word_threshold=50. Similarly, bm25_threshold=1.2 can be raised/lowered for more or fewer chunks in step two.
One-Pass Combination?
If your codebase or pipeline design allows applying multiple filters in one pass, you could do so. But often it’s simpler—and more transparent—to run them sequentially, analyzing each step’s result.

Bottom Line: By manually chaining your filtering logic in two passes, you get powerful incremental control over the final content. First, remove “global” clutter with Pruning, then refine further with BM25-based query relevance—without incurring a second network crawl.

8. Common Pitfalls & Tips
1. No Markdown Output?
- Make sure the crawler actually retrieved HTML. If the site is heavily JS-based, you may need to enable dynamic rendering or wait for elements.
- Check if your content filter is too aggressive. Lower thresholds or disable the filter to see if content reappears.

2. Performance Considerations
- Very large pages with multiple filters can be slower. Consider cache_mode to avoid re-downloading.
- If your final use case is LLM ingestion, consider summarizing further or chunking big texts.

3. Take Advantage of fit_markdown
- Great for RAG pipelines, semantic search, or any scenario where extraneous boilerplate is unwanted.
- Still verify the textual quality—some sites have crucial data in footers or sidebars.

4. Adjusting html2text Options
- If you see lots of raw HTML slipping into the text, turn on escape_html.
- If code blocks look messy, experiment with mark_code or handle_code_in_pre.


Fit Markdown with Pruning & BM25
Fit Markdown is a specialized filtered version of your page’s markdown, focusing on the most relevant content. By default, Crawl4AI converts the entire HTML into a broad raw_markdown. With fit markdown, we apply a content filter algorithm (e.g., Pruning or BM25) to remove or rank low-value sections—such as repetitive sidebars, shallow text blocks, or irrelevancies—leaving a concise textual “core.”

1. How “Fit Markdown” Works
1.1 The content_filter
In CrawlerRunConfig, you can specify a content_filter to shape how content is pruned or ranked before final markdown generation. A filter’s logic is applied before or during the HTML→Markdown process, producing:

result.markdown.raw_markdown (unfiltered)
result.markdown.fit_markdown (filtered or “fit” version)
result.markdown.fit_html (the corresponding HTML snippet that produced fit_markdown)
1.2 Common Filters
1. PruningContentFilter – Scores each node by text density, link density, and tag importance, discarding those below a threshold.
2. BM25ContentFilter – Focuses on textual relevance using BM25 ranking, especially useful if you have a specific user query (e.g., “machine learning” or “food nutrition”).

2. PruningContentFilter
Pruning discards less relevant nodes based on text density, link density, and tag importance. It’s a heuristic-based approach—if certain sections appear too “thin” or too “spammy,” they’re pruned.

2.1 Usage Example
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
        # Lower → more content retained, higher → more content pruned
        threshold=0.45,           
        # "fixed" or "dynamic"
        threshold_type="dynamic",  
        # Ignore nodes with <5 words
        min_word_threshold=5      
    )

    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # Step 3: Pass it to CrawlerRunConfig
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com", 
            config=config
        )

        if result.success:
            # 'fit_markdown' is your pruned content, focusing on "denser" text
            print("Raw Markdown length:", len(result.markdown.raw_markdown))
            print("Fit Markdown length:", len(result.markdown.fit_markdown))
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
2.2 Key Parameters
min_word_threshold (int): If a block has fewer words than this, it’s pruned.
threshold_type (str):
"fixed" → each node must exceed threshold (0–1).
"dynamic" → node scoring adjusts according to tag type, text/link density, etc.
threshold (float, default ~0.48): The base or “anchor” cutoff.
Algorithmic Factors:

Text density – Encourages blocks that have a higher ratio of text to overall content.
Link density – Penalizes sections that are mostly links.
Tag importance – e.g., an <article> or <p> might be more important than a <div>.
Structural context – If a node is deeply nested or in a suspected sidebar, it might be deprioritized.
3. BM25ContentFilter
BM25 is a classical text ranking algorithm often used in search engines. If you have a user query or rely on page metadata to derive a query, BM25 can identify which text chunks best match that query.

3.1 Usage Example
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    # 1) A BM25 filter with a user query
    bm25_filter = BM25ContentFilter(
        user_query="startup fundraising tips",
        # Adjust for stricter or looser results
        bm25_threshold=1.2  
    )

    # 2) Insert into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

    # 3) Pass to crawler config
    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com", 
            config=config
        )
        if result.success:
            print("Fit Markdown (BM25 query-based):")
            print(result.markdown.fit_markdown)
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
3.2 Parameters
user_query (str, optional): E.g. "machine learning". If blank, the filter tries to glean a query from page metadata.
bm25_threshold (float, default 1.0):
Higher → fewer chunks but more relevant.
Lower → more inclusive.
In more advanced scenarios, you might see parameters like use_stemming, case_sensitive, or priority_tags to refine how text is tokenized or weighted.

4. Accessing the “Fit” Output
After the crawl, your “fit” content is found in result.markdown.fit_markdown.

fit_md = result.markdown.fit_markdown
fit_html = result.markdown.fit_html
If the content filter is BM25, you might see additional logic or references in fit_markdown that highlight relevant segments. If it’s Pruning, the text is typically well-cleaned but not necessarily matched to a query.

5. Code Patterns Recap
5.1 Pruning
prune_filter = PruningContentFilter(
    threshold=0.5,
    threshold_type="fixed",
    min_word_threshold=10
)
md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
5.2 BM25
bm25_filter = BM25ContentFilter(
    user_query="health benefits fruit",
    bm25_threshold=1.2
)
md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)
config = CrawlerRunConfig(markdown_generator=md_generator)
6. Combining with “word_count_threshold” & Exclusions
Remember you can also specify:

config = CrawlerRunConfig(
    word_count_threshold=10,
    excluded_tags=["nav", "footer", "header"],
    exclude_external_links=True,
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)
    )
)
Thus, multi-level filtering occurs:

The crawler’s excluded_tags are removed from the HTML first.
The content filter (Pruning, BM25, or custom) prunes or ranks the remaining text blocks.
The final “fit” content is generated in result.markdown.fit_markdown.
7. Custom Filters
If you need a different approach (like a specialized ML model or site-specific heuristics), you can create a new class inheriting from RelevantContentFilter and implement filter_content(html). Then inject it into your markdown generator:

from crawl4ai.content_filter_strategy import RelevantContentFilter

class MyCustomFilter(RelevantContentFilter):
    def filter_content(self, html, min_word_threshold=None):
        # parse HTML, implement custom logic
        return [block for block in ... if ... some condition...]
Steps:

Subclass RelevantContentFilter.
Implement filter_content(...).
Use it in your DefaultMarkdownGenerator(content_filter=MyCustomFilter(...)).


Page Interaction
Crawl4AI provides powerful features for interacting with dynamic webpages, handling JavaScript execution, waiting for conditions, and managing multi-step flows. By combining js_code, wait_for, and certain CrawlerRunConfig parameters, you can:

Click “Load More” buttons
Fill forms and submit them
Wait for elements or data to appear
Reuse sessions across multiple steps
Below is a quick overview of how to do it.

1. JavaScript Execution
Basic Execution
js_code in CrawlerRunConfig accepts either a single JS string or a list of JS snippets.
Example: We’ll scroll to the bottom of the page, then optionally click a “Load More” button.

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Single JS command
    config = CrawlerRunConfig(
        js_code="window.scrollTo(0, document.body.scrollHeight);"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Example site
            config=config
        )
        print("Crawled length:", len(result.cleaned_html))

    # Multiple commands
    js_commands = [
        "window.scrollTo(0, document.body.scrollHeight);",
        # 'More' link on Hacker News
        "document.querySelector('a.morelink')?.click();",  
    ]
    config = CrawlerRunConfig(js_code=js_commands)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",  # Another pass
            config=config
        )
        print("After scroll+click, length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Relevant CrawlerRunConfig params: - js_code: A string or list of strings with JavaScript to run after the page loads. - js_only: If set to True on subsequent calls, indicates we’re continuing an existing session without a new full navigation.
- session_id: If you want to keep the same page across multiple calls, specify an ID.

2. Wait Conditions
2.1 CSS-Based Waiting
Sometimes, you just want to wait for a specific element to appear. For example:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Wait for at least 30 items on Hacker News
        wait_for="css:.athing:nth-child(30)"  
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("We have at least 30 items loaded!")
        # Rough check
        print("Total items in HTML:", result.cleaned_html.count("athing"))  

if __name__ == "__main__":
    asyncio.run(main())
Key param: - wait_for="css:...": Tells the crawler to wait until that CSS selector is present.

2.2 JavaScript-Based Waiting
For more complex conditions (e.g., waiting for content length to exceed a threshold), prefix js::

wait_condition = """() => {
    const items = document.querySelectorAll('.athing');
    return items.length > 50;  // Wait for at least 51 items
}"""

config = CrawlerRunConfig(wait_for=f"js:{wait_condition}")
Behind the Scenes: Crawl4AI keeps polling the JS function until it returns true or a timeout occurs.

3. Handling Dynamic Content
Many modern sites require multiple steps: scrolling, clicking “Load More,” or updating via JavaScript. Below are typical patterns.

3.1 Load More Example (Hacker News “More” Link)
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Step 1: Load initial Hacker News page
    config = CrawlerRunConfig(
        wait_for="css:.athing:nth-child(30)"  # Wait for 30 items
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com",
            config=config
        )
        print("Initial items loaded.")

        # Step 2: Let's scroll and click the "More" link
        load_more_js = [
            "window.scrollTo(0, document.body.scrollHeight);",
            # The "More" link at page bottom
            "document.querySelector('a.morelink')?.click();"  
        ]

        next_page_conf = CrawlerRunConfig(
            js_code=load_more_js,
            wait_for="""js:() => {
                return document.querySelectorAll('.athing').length > 30;
            }""",
            # Mark that we do not re-navigate, but run JS in the same session:
            js_only=True,
            session_id="hn_session"
        )

        # Re-use the same crawler session
        result2 = await crawler.arun(
            url="https://news.ycombinator.com",  # same URL but continuing session
            config=next_page_conf
        )
        total_items = result2.cleaned_html.count("athing")
        print("Items after load-more:", total_items)

if __name__ == "__main__":
    asyncio.run(main())
Key params: - session_id="hn_session": Keep the same page across multiple calls to arun(). - js_only=True: We’re not performing a full reload, just applying JS in the existing page. - wait_for with js:: Wait for item count to grow beyond 30.

3.2 Form Interaction
If the site has a search or login form, you can fill fields and submit them with js_code. For instance, if GitHub had a local search form:

js_form_interaction = """
document.querySelector('#your-search').value = 'TypeScript commits';
document.querySelector('form').submit();
"""

config = CrawlerRunConfig(
    js_code=js_form_interaction,
    wait_for="css:.commit"
)
result = await crawler.arun(url="https://github.com/search", config=config)
In reality: Replace IDs or classes with the real site’s form selectors.

4. Timing Control
1. page_timeout (ms): Overall page load or script execution time limit.
2. delay_before_return_html (seconds): Wait an extra moment before capturing the final HTML.
3. mean_delay & max_range: If you call arun_many() with multiple URLs, these add a random pause between each request.

Example:

config = CrawlerRunConfig(
    page_timeout=60000,  # 60s limit
    delay_before_return_html=2.5
)
5. Multi-Step Interaction Example
Below is a simplified script that does multiple “Load More” clicks on GitHub’s TypeScript commits page. It re-uses the same session to accumulate new commits each time. The code includes the relevant CrawlerRunConfig parameters you’d rely on.

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def multi_page_commits():
    browser_cfg = BrowserConfig(
        headless=False,  # Visible for demonstration
        verbose=True
    )
    session_id = "github_ts_commits"

    base_wait = """js:() => {
        const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
        return commits.length > 0;
    }"""

    # Step 1: Load initial commits
    config1 = CrawlerRunConfig(
        wait_for=base_wait,
        session_id=session_id,
        cache_mode=CacheMode.BYPASS,
        # Not using js_only yet since it's our first load
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://github.com/microsoft/TypeScript/commits/main",
            config=config1
        )
        print("Initial commits loaded. Count:", result.cleaned_html.count("commit"))

        # Step 2: For subsequent pages, we run JS to click 'Next Page' if it exists
        js_next_page = """
        const selector = 'a[data-testid="pagination-next-button"]';
        const button = document.querySelector(selector);
        if (button) button.click();
        """

        # Wait until new commits appear
        wait_for_more = """js:() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (!window.firstCommit && commits.length>0) {
                window.firstCommit = commits[0].textContent;
                return false;
            }
            // If top commit changes, we have new commits
            const topNow = commits[0]?.textContent.trim();
            return topNow && topNow !== window.firstCommit;
        }"""

        for page in range(2):  # let's do 2 more "Next" pages
            config_next = CrawlerRunConfig(
                session_id=session_id,
                js_code=js_next_page,
                wait_for=wait_for_more,
                js_only=True,       # We're continuing from the open tab
                cache_mode=CacheMode.BYPASS
            )
            result2 = await crawler.arun(
                url="https://github.com/microsoft/TypeScript/commits/main",
                config=config_next
            )
            print(f"Page {page+2} commits count:", result2.cleaned_html.count("commit"))

        # Optionally kill session
        await crawler.crawler_strategy.kill_session(session_id)

async def main():
    await multi_page_commits()

if __name__ == "__main__":
    asyncio.run(main())
Key Points:

session_id: Keep the same page open.
js_code + wait_for + js_only=True: We do partial refreshes, waiting for new commits to appear.
cache_mode=CacheMode.BYPASS ensures we always see fresh data each step.
6. Combine Interaction with Extraction
Once dynamic content is loaded, you can attach an extraction_strategy (like JsonCssExtractionStrategy or LLMExtractionStrategy). For example:

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "Commits",
    "baseSelector": "li.Box-sc-g0xbh4-0",
    "fields": [
        {"name": "title", "selector": "h4.markdown-title", "type": "text"}
    ]
}
config = CrawlerRunConfig(
    session_id="ts_commits_session",
    js_code=js_next_page,
    wait_for=wait_for_more,
    extraction_strategy=JsonCssExtractionStrategy(schema)
)
When done, check result.extracted_content for the JSON.

7. Relevant CrawlerRunConfig Parameters
Below are the key interaction-related parameters in CrawlerRunConfig. For a full list, see Configuration Parameters.

js_code: JavaScript to run after initial load.
js_only: If True, no new page navigation—only JS in the existing session.
wait_for: CSS ("css:...") or JS ("js:...") expression to wait for.
session_id: Reuse the same page across calls.
cache_mode: Whether to read/write from the cache or bypass.
remove_overlay_elements: Remove certain popups automatically.
simulate_user, override_navigator, magic: Anti-bot or “human-like” interactions.
8. Conclusion
Crawl4AI’s page interaction features let you:

1. Execute JavaScript for scrolling, clicks, or form filling.
2. Wait for CSS or custom JS conditions before capturing data.
3. Handle multi-step flows (like “Load More”) with partial reloads or persistent sessions.
4. Combine with structured extraction for dynamic sites.

Content Selection
Crawl4AI provides multiple ways to select, filter, and refine the content from your crawls. Whether you need to target a specific CSS region, exclude entire tags, filter out external links, or remove certain domains and images, CrawlerRunConfig offers a wide range of parameters.

Below, we show how to configure these parameters and combine them for precise control.

1. CSS-Based Selection
There are two ways to select content from a page: using css_selector or the more flexible target_elements.

1.1 Using css_selector
A straightforward way to limit your crawl results to a certain region of the page is css_selector in CrawlerRunConfig:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # e.g., first 30 items from Hacker News
        css_selector=".athing:nth-child(-n+30)"  
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest", 
            config=config
        )
        print("Partial HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Result: Only elements matching that selector remain in result.cleaned_html.

1.2 Using target_elements
The target_elements parameter provides more flexibility by allowing you to target multiple elements for content extraction while preserving the entire page context for other features:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Target article body and sidebar, but not other content
        target_elements=["article.main-content", "aside.sidebar"]
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/blog-post", 
            config=config
        )
        print("Markdown focused on target elements")
        print("Links from entire page still available:", len(result.links.get("internal", [])))

if __name__ == "__main__":
    asyncio.run(main())
Key difference: With target_elements, the markdown generation and structural data extraction focus on those elements, but other page elements (like links, images, and tables) are still extracted from the entire page. This gives you fine-grained control over what appears in your markdown content while preserving full page context for link analysis and media collection.

2. Content Filtering & Exclusions
2.1 Basic Overview
config = CrawlerRunConfig(
    # Content thresholds
    word_count_threshold=10,        # Minimum words per block

    # Tag exclusions
    excluded_tags=['form', 'header', 'footer', 'nav'],

    # Link filtering
    exclude_external_links=True,    
    exclude_social_media_links=True,
    # Block entire domains
    exclude_domains=["adtrackers.com", "spammynews.org"],    
    exclude_social_media_domains=["facebook.com", "twitter.com"],

    # Media filtering
    exclude_external_images=True
)
Explanation:

word_count_threshold: Ignores text blocks under X words. Helps skip trivial blocks like short nav or disclaimers.
excluded_tags: Removes entire tags (<form>, <header>, <footer>, etc.).
Link Filtering:
exclude_external_links: Strips out external links and may remove them from result.links.
exclude_social_media_links: Removes links pointing to known social media domains.
exclude_domains: A custom list of domains to block if discovered in links.
exclude_social_media_domains: A curated list (override or add to it) for social media sites.
Media Filtering:
exclude_external_images: Discards images not hosted on the same domain as the main page (or its subdomains).
By default in case you set exclude_social_media_links=True, the following social media domains are excluded:

[
    'facebook.com',
    'twitter.com',
    'x.com',
    'linkedin.com',
    'instagram.com',
    'pinterest.com',
    'tiktok.com',
    'snapchat.com',
    'reddit.com',
]
2.2 Example Usage
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(
        css_selector="main.content", 
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_domains=["ads.com", "spammytrackers.net"],
        exclude_external_images=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        print("Cleaned HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Note: If these parameters remove too much, reduce or disable them accordingly.

3. Handling Iframes
Some sites embed content in <iframe> tags. If you want that inline:

config = CrawlerRunConfig(
    # Merge iframe content into the final output
    process_iframes=True,    
    remove_overlay_elements=True
)
Usage:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        process_iframes=True,
        remove_overlay_elements=True
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.org/iframe-demo", 
            config=config
        )
        print("Iframe-merged length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
4. Structured Extraction Examples
You can combine content selection with a more advanced extraction strategy. For instance, a CSS-based or LLM-based extraction strategy can run on the filtered HTML.

4.1 Pattern-Based with JsonCssExtractionStrategy
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    # Minimal schema for repeated items
    schema = {
        "name": "News Items",
        "baseSelector": "tr.athing",
        "fields": [
            {"name": "title", "selector": "span.titleline a", "type": "text"},
            {
                "name": "link", 
                "selector": "span.titleline a", 
                "type": "attribute", 
                "attribute": "href"
            }
        ]
    }

    config = CrawlerRunConfig(
        # Content filtering
        excluded_tags=["form", "header"],
        exclude_domains=["adsite.com"],

        # CSS selection or entire page
        css_selector="table.itemlist",

        # No caching for demonstration
        cache_mode=CacheMode.BYPASS,

        # Extraction strategy
        extraction_strategy=JsonCssExtractionStrategy(schema)
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest", 
            config=config
        )
        data = json.loads(result.extracted_content)
        print("Sample extracted item:", data[:1])  # Show first item

if __name__ == "__main__":
    asyncio.run(main())
4.2 LLM-Based Extraction
import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class ArticleData(BaseModel):
    headline: str
    summary: str

async def main():
    llm_strategy = LLMExtractionStrategy(
        llm_config = LLMConfig(provider="openai/gpt-4",api_token="sk-YOUR_API_KEY")
        schema=ArticleData.schema(),
        extraction_type="schema",
        instruction="Extract 'headline' and a short 'summary' from the content."
    )

    config = CrawlerRunConfig(
        exclude_external_links=True,
        word_count_threshold=20,
        extraction_strategy=llm_strategy
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        article = json.loads(result.extracted_content)
        print(article)

if __name__ == "__main__":
    asyncio.run(main())
Here, the crawler:

Filters out external links (exclude_external_links=True).
Ignores very short text blocks (word_count_threshold=20).
Passes the final HTML to your LLM strategy for an AI-driven parse.
5. Comprehensive Example
Below is a short function that unifies CSS selection, exclusion logic, and a pattern-based extraction, demonstrating how you can fine-tune your final data:

import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_main_articles(url: str):
    schema = {
        "name": "ArticleBlock",
        "baseSelector": "div.article-block",
        "fields": [
            {"name": "headline", "selector": "h2", "type": "text"},
            {"name": "summary", "selector": ".summary", "type": "text"},
            {
                "name": "metadata",
                "type": "nested",
                "fields": [
                    {"name": "author", "selector": ".author", "type": "text"},
                    {"name": "date", "selector": ".date", "type": "text"}
                ]
            }
        ]
    }

    config = CrawlerRunConfig(
        # Keep only #main-content
        css_selector="#main-content",

        # Filtering
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],  
        exclude_external_links=True,
        exclude_domains=["somebadsite.com"],
        exclude_external_images=True,

        # Extraction
        extraction_strategy=JsonCssExtractionStrategy(schema),

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            print(f"Error: {result.error_message}")
            return None
        return json.loads(result.extracted_content)

async def main():
    articles = await extract_main_articles("https://news.ycombinator.com/newest")
    if articles:
        print("Extracted Articles:", articles[:2])  # Show first 2

if __name__ == "__main__":
    asyncio.run(main())
Why This Works: - CSS scoping with #main-content.
- Multiple exclude_ parameters to remove domains, external images, etc.
- A JsonCssExtractionStrategy to parse repeated article blocks.

6. Scraping Modes
Crawl4AI provides two different scraping strategies for HTML content processing: WebScrapingStrategy (BeautifulSoup-based, default) and LXMLWebScrapingStrategy (LXML-based). The LXML strategy offers significantly better performance, especially for large HTML documents.

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LXMLWebScrapingStrategy

async def main():
    config = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy()  # Faster alternative to default BeautifulSoup
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com", 
            config=config
        )
You can also create your own custom scraping strategy by inheriting from ContentScrapingStrategy. The strategy must return a ScrapingResult object with the following structure:

from crawl4ai import ContentScrapingStrategy, ScrapingResult, MediaItem, Media, Link, Links

class CustomScrapingStrategy(ContentScrapingStrategy):
    def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # Implement your custom scraping logic here
        return ScrapingResult(
            cleaned_html="<html>...</html>",  # Cleaned HTML content
            success=True,                     # Whether scraping was successful
            media=Media(
                images=[                      # List of images found
                    MediaItem(
                        src="https://example.com/image.jpg",
                        alt="Image description",
                        desc="Surrounding text",
                        score=1,
                        type="image",
                        group_id=1,
                        format="jpg",
                        width=800
                    )
                ],
                videos=[],                    # List of videos (same structure as images)
                audios=[]                     # List of audio files (same structure as images)
            ),
            links=Links(
                internal=[                    # List of internal links
                    Link(
                        href="https://example.com/page",
                        text="Link text",
                        title="Link title",
                        base_domain="example.com"
                    )
                ],
                external=[]                   # List of external links (same structure)
            ),
            metadata={                        # Additional metadata
                "title": "Page Title",
                "description": "Page description"
            }
        )

    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # For simple cases, you can use the sync version
        return await asyncio.to_thread(self.scrap, url, html, **kwargs)
Performance Considerations
The LXML strategy can be up to 10-20x faster than BeautifulSoup strategy, particularly when processing large HTML documents. However, please note:

LXML strategy is currently experimental
In some edge cases, the parsing results might differ slightly from BeautifulSoup
If you encounter any inconsistencies between LXML and BeautifulSoup results, please raise an issue with a reproducible example
Choose LXML strategy when: - Processing large HTML documents (recommended for >100KB) - Performance is critical - Working with well-formed HTML

Stick to BeautifulSoup strategy (default) when: - Maximum compatibility is needed - Working with malformed HTML - Exact parsing behavior is critical

7. Combining CSS Selection Methods
You can combine css_selector and target_elements in powerful ways to achieve fine-grained control over your output:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    # Target specific content but preserve page context
    config = CrawlerRunConfig(
        # Focus markdown on main content and sidebar
        target_elements=["#main-content", ".sidebar"],

        # Global filters applied to entire page
        excluded_tags=["nav", "footer", "header"],
        exclude_external_links=True,

        # Use basic content thresholds
        word_count_threshold=15,

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/article",
            config=config
        )

        print(f"Content focuses on specific elements, but all links still analyzed")
        print(f"Internal links: {len(result.links.get('internal', []))}")
        print(f"External links: {len(result.links.get('external', []))}")

if __name__ == "__main__":
    asyncio.run(main())
This approach gives you the best of both worlds: - Markdown generation and content extraction focus on the elements you care about - Links, images and other page data still give you the full context of the page - Content filtering still applies globally

8. Conclusion
By mixing target_elements or css_selector scoping, content filtering parameters, and advanced extraction strategies, you can precisely choose which data to keep. Key parameters in CrawlerRunConfig for content selection include:

target_elements – Array of CSS selectors to focus markdown generation and data extraction, while preserving full page context for links and media.
css_selector – Basic scoping to an element or region for all extraction processes.
word_count_threshold – Skip short blocks.
excluded_tags – Remove entire HTML tags.
exclude_external_links, exclude_social_media_links, exclude_domains – Filter out unwanted links or domains.
exclude_external_images – Remove images from external sources.
process_iframes – Merge iframe content if needed.


Crawl4AI Cache System and Migration Guide
Overview
Starting from version 0.5.0, Crawl4AI introduces a new caching system that replaces the old boolean flags with a more intuitive CacheMode enum. This change simplifies cache control and makes the behavior more predictable.

Old vs New Approach
Old Way (Deprecated)
The old system used multiple boolean flags: - bypass_cache: Skip cache entirely - disable_cache: Disable all caching - no_cache_read: Don't read from cache - no_cache_write: Don't write to cache

New Way (Recommended)
The new system uses a single CacheMode enum: - CacheMode.ENABLED: Normal caching (read/write) - CacheMode.DISABLED: No caching at all - CacheMode.READ_ONLY: Only read from cache - CacheMode.WRITE_ONLY: Only write to cache - CacheMode.BYPASS: Skip cache for this operation

Migration Example
Old Code (Deprecated)
import asyncio
from crawl4ai import AsyncWebCrawler

async def use_proxy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            bypass_cache=True  # Old way
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
New Code (Recommended)
import asyncio
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig

async def use_proxy():
    # Use CacheMode in CrawlerRunConfig
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)  
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            config=config  # Pass the configuration object
        )
        print(len(result.markdown))

async def main():
    await use_proxy()

if __name__ == "__main__":
    asyncio.run(main())
Common Migration Patterns
Old Flag	New Mode
bypass_cache=True	cache_mode=CacheMode.BYPASS
disable_cache=True	cache_mode=CacheMode.DISABLED
no_cache_read=True	cache_mode=CacheMode.WRITE_ONLY
no_cache_write=True	cache_mode=CacheMode.READ_ONLY

Prefix-Based Input Handling in Crawl4AI
This guide will walk you through using the Crawl4AI library to crawl web pages, local HTML files, and raw HTML strings. We'll demonstrate these capabilities using a Wikipedia page as an example.

Crawling a Web URL
To crawl a live web page, provide the URL starting with http:// or https://, using a CrawlerRunConfig object:

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_web():
    config = CrawlerRunConfig(bypass_cache=True)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/apple", 
            config=config
        )
        if result.success:
            print("Markdown Content:")
            print(result.markdown)
        else:
            print(f"Failed to crawl: {result.error_message}")

asyncio.run(crawl_web())
Crawling a Local HTML File
To crawl a local HTML file, prefix the file path with file://.

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_local_file():
    local_file_path = "/path/to/apple.html"  # Replace with your file path
    file_url = f"file://{local_file_path}"
    config = CrawlerRunConfig(bypass_cache=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=file_url, config=config)
        if result.success:
            print("Markdown Content from Local File:")
            print(result.markdown)
        else:
            print(f"Failed to crawl local file: {result.error_message}")

asyncio.run(crawl_local_file())
Crawling Raw HTML Content
To crawl raw HTML content, prefix the HTML string with raw:.

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def crawl_raw_html():
    raw_html = "<html><body><h1>Hello, World!</h1></body></html>"
    raw_html_url = f"raw:{raw_html}"
    config = CrawlerRunConfig(bypass_cache=True)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=raw_html_url, config=config)
        if result.success:
            print("Markdown Content from Raw HTML:")
            print(result.markdown)
        else:
            print(f"Failed to crawl raw HTML: {result.error_message}")

asyncio.run(crawl_raw_html())
Complete Example
Below is a comprehensive script that:

Crawls the Wikipedia page for "Apple."
Saves the HTML content to a local file (apple.html).
Crawls the local HTML file and verifies the markdown length matches the original crawl.
Crawls the raw HTML content from the saved file and verifies consistency.
import os
import sys
import asyncio
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig

async def main():
    wikipedia_url = "https://en.wikipedia.org/wiki/apple"
    script_dir = Path(__file__).parent
    html_file_path = script_dir / "apple.html"

    async with AsyncWebCrawler() as crawler:
        # Step 1: Crawl the Web URL
        print("\n=== Step 1: Crawling the Wikipedia URL ===")
        web_config = CrawlerRunConfig(bypass_cache=True)
        result = await crawler.arun(url=wikipedia_url, config=web_config)

        if not result.success:
            print(f"Failed to crawl {wikipedia_url}: {result.error_message}")
            return

        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(result.html)
        web_crawl_length = len(result.markdown)
        print(f"Length of markdown from web crawl: {web_crawl_length}\n")

        # Step 2: Crawl from the Local HTML File
        print("=== Step 2: Crawling from the Local HTML File ===")
        file_url = f"file://{html_file_path.resolve()}"
        file_config = CrawlerRunConfig(bypass_cache=True)
        local_result = await crawler.arun(url=file_url, config=file_config)

        if not local_result.success:
            print(f"Failed to crawl local file {file_url}: {local_result.error_message}")
            return

        local_crawl_length = len(local_result.markdown)
        assert web_crawl_length == local_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and local file crawl.\n")

        # Step 3: Crawl Using Raw HTML Content
        print("=== Step 3: Crawling Using Raw HTML Content ===")
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        raw_html_url = f"raw:{raw_html_content}"
        raw_config = CrawlerRunConfig(bypass_cache=True)
        raw_result = await crawler.arun(url=raw_html_url, config=raw_config)

        if not raw_result.success:
            print(f"Failed to crawl raw HTML content: {raw_result.error_message}")
            return

        raw_crawl_length = len(raw_result.markdown)
        assert web_crawl_length == raw_crawl_length, "Markdown length mismatch"
        print("✅ Markdown length matches between web and raw HTML crawl.\n")

        print("All tests passed successfully!")
    if html_file_path.exists():
        os.remove(html_file_path)

if __name__ == "__main__":
    asyncio.run(main())

    Link & Media
In this tutorial, you’ll learn how to:

Extract links (internal, external) from crawled pages
Filter or exclude specific domains (e.g., social media or custom domains)
Access and manage media data (especially images) in the crawl result
Configure your crawler to exclude or prioritize certain images
Prerequisites
- You have completed or are familiar with the AsyncWebCrawler Basics tutorial.
- You can run Crawl4AI in your environment (Playwright, Python, etc.).

Below is a revised version of the Link Extraction and Media Extraction sections that includes example data structures showing how links and media items are stored in CrawlResult. Feel free to adjust any field names or descriptions to match your actual output.

1. Link Extraction
1.1 result.links
When you call arun() or arun_many() on a URL, Crawl4AI automatically extracts links and stores them in the links field of CrawlResult. By default, the crawler tries to distinguish internal links (same domain) from external links (different domains).

Basic Example:

from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://www.example.com")
    if result.success:
        internal_links = result.links.get("internal", [])
        external_links = result.links.get("external", [])
        print(f"Found {len(internal_links)} internal links.")
        print(f"Found {len(internal_links)} external links.")
        print(f"Found {len(result.media)} media items.")

        # Each link is typically a dictionary with fields like:
        # { "href": "...", "text": "...", "title": "...", "base_domain": "..." }
        if internal_links:
            print("Sample Internal Link:", internal_links[0])
    else:
        print("Crawl failed:", result.error_message)
Structure Example:

result.links = {
  "internal": [
    {
      "href": "https://kidocode.com/",
      "text": "",
      "title": "",
      "base_domain": "kidocode.com"
    },
    {
      "href": "https://kidocode.com/degrees/technology",
      "text": "Technology Degree",
      "title": "KidoCode Tech Program",
      "base_domain": "kidocode.com"
    },
    # ...
  ],
  "external": [
    # possibly other links leading to third-party sites
  ]
}
href: The raw hyperlink URL.
text: The link text (if any) within the <a> tag.
title: The title attribute of the link (if present).
base_domain: The domain extracted from href. Helpful for filtering or grouping by domain.
2. Domain Filtering
Some websites contain hundreds of third-party or affiliate links. You can filter out certain domains at crawl time by configuring the crawler. The most relevant parameters in CrawlerRunConfig are:

exclude_external_links: If True, discard any link pointing outside the root domain.
exclude_social_media_domains: Provide a list of social media platforms (e.g., ["facebook.com", "twitter.com"]) to exclude from your crawl.
exclude_social_media_links: If True, automatically skip known social platforms.
exclude_domains: Provide a list of custom domains you want to exclude (e.g., ["spammyads.com", "tracker.net"]).
2.1 Example: Excluding External & Social Media Links
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,          # No links outside primary domain
        exclude_social_media_links=True       # Skip recognized social media domains
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://www.example.com",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Crawled:", result.url)
            print("Internal links count:", len(result.links.get("internal", [])))
            print("External links count:", len(result.links.get("external", [])))  
            # Likely zero external links in this scenario
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
2.2 Example: Excluding Specific Domains
If you want to let external links in, but specifically exclude a domain (e.g., suspiciousads.com), do this:

crawler_cfg = CrawlerRunConfig(
    exclude_domains=["suspiciousads.com"]
)
This approach is handy when you still want external links but need to block certain sites you consider spammy.

3. Media Extraction
3.1 Accessing result.media
By default, Crawl4AI collects images, audio, video URLs, and data tables it finds on the page. These are stored in result.media, a dictionary keyed by media type (e.g., images, videos, audio, tables).

Basic Example:

if result.success:
    # Get images
    images_info = result.media.get("images", [])
    print(f"Found {len(images_info)} images in total.")
    for i, img in enumerate(images_info[:3]):  # Inspect just the first 3
        print(f"[Image {i}] URL: {img['src']}")
        print(f"           Alt text: {img.get('alt', '')}")
        print(f"           Score: {img.get('score')}")
        print(f"           Description: {img.get('desc', '')}\n")

    # Get tables
    tables = result.media.get("tables", [])
    print(f"Found {len(tables)} data tables in total.")
    for i, table in enumerate(tables):
        print(f"[Table {i}] Caption: {table.get('caption', 'No caption')}")
        print(f"           Columns: {len(table.get('headers', []))}")
        print(f"           Rows: {len(table.get('rows', []))}")
Structure Example:

result.media = {
  "images": [
    {
      "src": "https://cdn.prod.website-files.com/.../Group%2089.svg",
      "alt": "coding school for kids",
      "desc": "Trial Class Degrees degrees All Degrees AI Degree Technology ...",
      "score": 3,
      "type": "image",
      "group_id": 0,
      "format": None,
      "width": None,
      "height": None
    },
    # ...
  ],
  "videos": [
    # Similar structure but with video-specific fields
  ],
  "audio": [
    # Similar structure but with audio-specific fields
  ],
  "tables": [
    {
      "headers": ["Name", "Age", "Location"],
      "rows": [
        ["John Doe", "34", "New York"],
        ["Jane Smith", "28", "San Francisco"],
        ["Alex Johnson", "42", "Chicago"]
      ],
      "caption": "Employee Directory",
      "summary": "Directory of company employees"
    },
    # More tables if present
  ]
}
Depending on your Crawl4AI version or scraping strategy, these dictionaries can include fields like:

src: The media URL (e.g., image source)
alt: The alt text for images (if present)
desc: A snippet of nearby text or a short description (optional)
score: A heuristic relevance score if you’re using content-scoring features
width, height: If the crawler detects dimensions for the image/video
type: Usually "image", "video", or "audio"
group_id: If you’re grouping related media items, the crawler might assign an ID
With these details, you can easily filter out or focus on certain images (for instance, ignoring images with very low scores or a different domain), or gather metadata for analytics.

3.2 Excluding External Images
If you’re dealing with heavy pages or want to skip third-party images (advertisements, for example), you can turn on:

crawler_cfg = CrawlerRunConfig(
    exclude_external_images=True
)
This setting attempts to discard images from outside the primary domain, keeping only those from the site you’re crawling.

3.3 Working with Tables
Crawl4AI can detect and extract structured data from HTML tables. Tables are analyzed based on various criteria to determine if they are actual data tables (as opposed to layout tables), including:

Presence of thead and tbody sections
Use of th elements for headers
Column consistency
Text density
And other factors
Tables that score above the threshold (default: 7) are extracted and stored in result.media.tables.

Accessing Table Data:

if result.success:
    tables = result.media.get("tables", [])
    print(f"Found {len(tables)} data tables on the page")

    if tables:
        # Access the first table
        first_table = tables[0]
        print(f"Table caption: {first_table.get('caption', 'No caption')}")
        print(f"Headers: {first_table.get('headers', [])}")

        # Print the first 3 rows
        for i, row in enumerate(first_table.get('rows', [])[:3]):
            print(f"Row {i+1}: {row}")
Configuring Table Extraction:

You can adjust the sensitivity of the table detection algorithm with:

crawler_cfg = CrawlerRunConfig(
    table_score_threshold=5  # Lower value = more tables detected (default: 7)
)
Each extracted table contains: - headers: Column header names - rows: List of rows, each containing cell values - caption: Table caption text (if available) - summary: Table summary attribute (if specified)

3.4 Additional Media Config
screenshot: Set to True if you want a full-page screenshot stored as base64 in result.screenshot.
pdf: Set to True if you want a PDF version of the page in result.pdf.
wait_for_images: If True, attempts to wait until images are fully loaded before final extraction.
4. Putting It All Together: Link & Media Filtering
Here’s a combined example demonstrating how to filter out external links, skip certain domains, and exclude external images:

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    # Suppose we want to keep only internal links, remove certain domains, 
    # and discard external images from the final crawl data.
    crawler_cfg = CrawlerRunConfig(
        exclude_external_links=True,
        exclude_domains=["spammyads.com"],
        exclude_social_media_links=True,   # skip Twitter, Facebook, etc.
        exclude_external_images=True,      # keep only images from main domain
        wait_for_images=True,             # ensure images are loaded
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://www.example.com", config=crawler_cfg)

        if result.success:
            print("[OK] Crawled:", result.url)

            # 1. Links
            in_links = result.links.get("internal", [])
            ext_links = result.links.get("external", [])
            print("Internal link count:", len(in_links))
            print("External link count:", len(ext_links))  # should be zero with exclude_external_links=True

            # 2. Images
            images = result.media.get("images", [])
            print("Images found:", len(images))

            # Let's see a snippet of these images
            for i, img in enumerate(images[:3]):
                print(f"  - {img['src']} (alt={img.get('alt','')}, score={img.get('score','N/A')})")
        else:
            print("[ERROR] Failed to crawl. Reason:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
5. Common Pitfalls & Tips
1. Conflicting Flags:
- exclude_external_links=True but then also specifying exclude_social_media_links=True is typically fine, but understand that the first setting already discards all external links. The second becomes somewhat redundant.
- exclude_external_images=True but want to keep some external images? Currently no partial domain-based setting for images, so you might need a custom approach or hook logic.

2. Relevancy Scores:
- If your version of Crawl4AI or your scraping strategy includes an img["score"], it’s typically a heuristic based on size, position, or content analysis. Evaluate carefully if you rely on it.

3. Performance:
- Excluding certain domains or external images can speed up your crawl, especially for large, media-heavy pages.
- If you want a “full” link map, do not exclude them. Instead, you can post-filter in your own code.

4. Social Media Lists:
- exclude_social_media_links=True typically references an internal list of known social domains like Facebook, Twitter, LinkedIn, etc. If you need to add or remove from that list, look for library settings or a local config file (depending on your version).

That’s it for Link & Media Analysis! You’re now equipped to filter out unwanted sites and zero in on the images and videos that matter for your project.

Table Extraction Tips
Not all HTML tables are extracted - only those detected as "data tables" vs. layout tables.
Tables with inconsistent cell counts, nested tables, or those used purely for layout may be skipped.
If you're missing tables, try adjusting the table_score_threshold to a lower value (default is 7).

Overview of Some Important Advanced Features
(Proxy, PDF, Screenshot, SSL, Headers, & Storage State)

Crawl4AI offers multiple power-user features that go beyond simple crawling. This tutorial covers:

1. Proxy Usage
2. Capturing PDFs & Screenshots
3. Handling SSL Certificates
4. Custom Headers
5. Session Persistence & Local Storage
6. Robots.txt Compliance

Prerequisites
- You have a basic grasp of AsyncWebCrawler Basics
- You know how to run or configure your Python environment with Playwright installed

1. Proxy Usage
If you need to route your crawl traffic through a proxy—whether for IP rotation, geo-testing, or privacy—Crawl4AI supports it via BrowserConfig.proxy_config.

import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True
    )
    crawler_cfg = CrawlerRunConfig(
        verbose=True
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url="https://www.whatismyip.com/",
            config=crawler_cfg
        )
        if result.success:
            print("[OK] Page fetched via proxy.")
            print("Page HTML snippet:", result.html[:200])
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Key Points
- proxy_config expects a dict with server and optional auth credentials.
- Many commercial proxies provide an HTTP/HTTPS “gateway” server that you specify in server.
- If your proxy doesn’t need auth, omit username/password.

2. Capturing PDFs & Screenshots
Sometimes you need a visual record of a page or a PDF “printout.” Crawl4AI can do both in one pass:

import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CacheMode

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/List_of_common_misconceptions",
            cache_mode=CacheMode.BYPASS,
            pdf=True,
            screenshot=True
        )

        if result.success:
            # Save screenshot
            if result.screenshot:
                with open("wikipedia_screenshot.png", "wb") as f:
                    f.write(b64decode(result.screenshot))

            # Save PDF
            if result.pdf:
                with open("wikipedia_page.pdf", "wb") as f:
                    f.write(result.pdf)

            print("[OK] PDF & screenshot captured.")
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Why PDF + Screenshot?
- Large or complex pages can be slow or error-prone with “traditional” full-page screenshots.
- Exporting a PDF is more reliable for very long pages. Crawl4AI automatically converts the first PDF page into an image if you request both.

Relevant Parameters
- pdf=True: Exports the current page as a PDF (base64-encoded in result.pdf).
- screenshot=True: Creates a screenshot (base64-encoded in result.screenshot).
- scan_full_page or advanced hooking can further refine how the crawler captures content.

3. Handling SSL Certificates
If you need to verify or export a site’s SSL certificate—for compliance, debugging, or data analysis—Crawl4AI can fetch it during the crawl:

import asyncio, os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)

        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            print("\nCertificate Information:")
            print(f"Issuer (CN): {cert.issuer.get('CN', '')}")
            print(f"Valid until: {cert.valid_until}")
            print(f"Fingerprint: {cert.fingerprint}")

            # Export in multiple formats:
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))
            cert.to_pem(os.path.join(tmp_dir, "certificate.pem"))
            cert.to_der(os.path.join(tmp_dir, "certificate.der"))

            print("\nCertificate exported to JSON/PEM/DER in 'tmp' folder.")
        else:
            print("[ERROR] No certificate or crawl failed.")

if __name__ == "__main__":
    asyncio.run(main())
Key Points
- fetch_ssl_certificate=True triggers certificate retrieval.
- result.ssl_certificate includes methods (to_json, to_pem, to_der) for saving in various formats (handy for server config, Java keystores, etc.).

4. Custom Headers
Sometimes you need to set custom headers (e.g., language preferences, authentication tokens, or specialized user-agent strings). You can do this in multiple ways:

import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Option 1: Set headers at the crawler strategy level
    crawler1 = AsyncWebCrawler(
        # The underlying strategy can accept headers in its constructor
        crawler_strategy=None  # We'll override below for clarity
    )
    crawler1.crawler_strategy.update_user_agent("MyCustomUA/1.0")
    crawler1.crawler_strategy.set_custom_headers({
        "Accept-Language": "fr-FR,fr;q=0.9"
    })
    result1 = await crawler1.arun("https://www.example.com")
    print("Example 1 result success:", result1.success)

    # Option 2: Pass headers directly to `arun()`
    crawler2 = AsyncWebCrawler()
    result2 = await crawler2.arun(
        url="https://www.example.com",
        headers={"Accept-Language": "es-ES,es;q=0.9"}
    )
    print("Example 2 result success:", result2.success)

if __name__ == "__main__":
    asyncio.run(main())
Notes
- Some sites may react differently to certain headers (e.g., Accept-Language).
- If you need advanced user-agent randomization or client hints, see Identity-Based Crawling (Anti-Bot) or use UserAgentGenerator.

5. Session Persistence & Local Storage
Crawl4AI can preserve cookies and localStorage so you can continue where you left off—ideal for logging into sites or skipping repeated auth flows.

5.1 storage_state
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    storage_dict = {
        "cookies": [
            {
                "name": "session",
                "value": "abcd1234",
                "domain": "example.com",
                "path": "/",
                "expires": 1699999999.0,
                "httpOnly": False,
                "secure": False,
                "sameSite": "None"
            }
        ],
        "origins": [
            {
                "origin": "https://example.com",
                "localStorage": [
                    {"name": "token", "value": "my_auth_token"}
                ]
            }
        ]
    }

    # Provide the storage state as a dictionary to start "already logged in"
    async with AsyncWebCrawler(
        headless=True,
        storage_state=storage_dict
    ) as crawler:
        result = await crawler.arun("https://example.com/protected")
        if result.success:
            print("Protected page content length:", len(result.html))
        else:
            print("Failed to crawl protected page")

if __name__ == "__main__":
    asyncio.run(main())
5.2 Exporting & Reusing State
You can sign in once, export the browser context, and reuse it later—without re-entering credentials.

await context.storage_state(path="my_storage.json"): Exports cookies, localStorage, etc. to a file.
Provide storage_state="my_storage.json" on subsequent runs to skip the login step.
See: Detailed session management tutorial or Explanations → Browser Context & Managed Browser for more advanced scenarios (like multi-step logins, or capturing after interactive pages).

6. Robots.txt Compliance
Crawl4AI supports respecting robots.txt rules with efficient caching:

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    # Enable robots.txt checking in config
    config = CrawlerRunConfig(
        check_robots_txt=True  # Will check and respect robots.txt rules
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=config
        )

        if not result.success and result.status_code == 403:
            print("Access denied by robots.txt")

if __name__ == "__main__":
    asyncio.run(main())
Key Points - Robots.txt files are cached locally for efficiency - Cache is stored in ~/.crawl4ai/robots/robots_cache.db - Cache has a default TTL of 7 days - If robots.txt can't be fetched, crawling is allowed - Returns 403 status code if URL is disallowed

Putting It All Together
Here’s a snippet that combines multiple “advanced” features (proxy, PDF, screenshot, SSL, custom headers, and session reuse) into one run. Normally, you’d tailor each setting to your project’s needs.

import os, asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # 1. Browser config with proxy + headless
    browser_cfg = BrowserConfig(
        proxy_config={
            "server": "http://proxy.example.com:8080",
            "username": "myuser",
            "password": "mypass",
        },
        headless=True,
    )

    # 2. Crawler config with PDF, screenshot, SSL, custom headers, and ignoring caches
    crawler_cfg = CrawlerRunConfig(
        pdf=True,
        screenshot=True,
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS,
        headers={"Accept-Language": "en-US,en;q=0.8"},
        storage_state="my_storage.json",  # Reuse session from a previous sign-in
        verbose=True,
    )

    # 3. Crawl
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url = "https://secure.example.com/protected", 
            config=crawler_cfg
        )

        if result.success:
            print("[OK] Crawled the secure page. Links found:", len(result.links.get("internal", [])))

            # Save PDF & screenshot
            if result.pdf:
                with open("result.pdf", "wb") as f:
                    f.write(b64decode(result.pdf))
            if result.screenshot:
                with open("result.png", "wb") as f:
                    f.write(b64decode(result.screenshot))

            # Check SSL cert
            if result.ssl_certificate:
                print("SSL Issuer CN:", result.ssl_certificate.issuer.get("CN", ""))
        else:
            print("[ERROR]", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
Conclusion & Next Steps
You’ve now explored several advanced features:

Proxy Usage
PDF & Screenshot capturing for large or critical pages
SSL Certificate retrieval & exporting
Custom Headers for language or specialized requests
Session Persistence via storage state
Robots.txt Compliance
With these power tools, you can build robust scraping workflows that mimic real user behavior, handle secure sites, capture detailed snapshots, and manage sessions across multiple runs—streamlining your entire data collection pipeline.