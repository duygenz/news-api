import asyncio
import aiohttp
from newspaper import Article, Config
import feedparser
import re
from datetime import datetime, timedelta
import hashlib

# Cache đơn giản lưu trữ 1 giờ
NEWS_CACHE = {}
CACHE_EXPIRY = timedelta(hours=1)

def fetch_full_content(url):
    """Lấy toàn bộ nội dung bài viết từ URL sử dụng newspaper3k"""
    try:
        config = Config()
        config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        config.request_timeout = 10
        
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        return article.text
    except Exception as e:
        print(f"Error fetching content: {e}")
        return ""

def split_into_chunks(text, chunk_size=500):
    """Chia văn bản thành các chunks với kích thước xác định"""
    if not text:
        return []
    
    clean_text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

async def async_fetch_feed(session, rss_url):
    """Lấy nội dung RSS feed bất đồng bộ"""
    cache_key = hashlib.md5(rss_url.encode()).hexdigest()
    
    # Kiểm tra cache
    if cache_key in NEWS_CACHE:
        cached_time, data = NEWS_CACHE[cache_key]
        if datetime.now() - cached_time < CACHE_EXPIRY:
            return data
    
    try:
        async with session.get(rss_url) as response:
            content = await response.text()
            feed = feedparser.parse(content)
            
            news_items = []
            for entry in feed.entries[:5]:
                full_content = fetch_full_content(entry.link)
                chunks = split_into_chunks(full_content)
                
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", ""),
                    "source": rss_url,
                    "chunks": chunks
                })
            
            # Lưu vào cache
            NEWS_CACHE[cache_key] = (datetime.now(), news_items)
            return news_items
            
    except Exception as e:
        print(f"Error fetching {rss_url}: {e}")
        return []