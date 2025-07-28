import feedparser
import requests
from bs4 import BeautifulSoup
import re
from newspaper import Article, Config

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
    
    # Chuẩn hóa khoảng trắng
    clean_text = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    
    start = 0
    while start < len(clean_text):
        end = start + chunk_size
        if end >= len(clean_text):
            chunks.append(clean_text[start:])
            break
        
        # Tìm vị trí cắt tự nhiên (dấu câu hoặc khoảng trắng)
        while end > start and clean_text[end] not in (' ', '.', '!', '?', ','):
            end -= 1
        
        if end == start:  # Trường hợp không tìm thấy vị trí cắt
            end = start + chunk_size
            
        chunks.append(clean_text[start:end].strip())
        start = end + 1
        
    return chunks

def get_news_from_rss(rss_url):
    """Lấy tin tức từ RSS feed và xử lý nội dung"""
    news_items = []
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries[:5]:  # Giới hạn 5 bài mỗi nguồn
        try:
            full_content = fetch_full_content(entry.link)
            chunks = split_into_chunks(full_content)
            
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", ""),
                "source": rss_url,
                "chunks": chunks
            })
        except Exception as e:
            print(f"Error processing {entry.link}: {e}")
    
    return news_items
