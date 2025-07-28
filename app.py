from flask import Flask, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time
from urllib.parse import urljoin, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

app = Flask(**name**)

# RSS feeds configuration

RSS_FEEDS = {
‘vietstock_stocks’: ‘https://vietstock.vn/830/chung-khoan/co-phieu.rss’,
‘cafef_market’: ‘https://cafef.vn/thi-truong-chung-khoan.rss’,
‘vietstock_expert’: ‘https://vietstock.vn/145/chung-khoan/y-kien-chuyen-gia.rss’,
‘vietstock_business’: ‘https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss’,
‘vietstock_dongduong’: ‘https://vietstock.vn/1328/dong-duong/thi-truong-chung-khoan.rss’
}

class NewsExtractor:
def **init**(self):
self.session = requests.Session()
self.session.headers.update({
‘User-Agent’: ‘Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36’
})

```
def get_full_article_content(self, url):
    """Extract full article content from URL"""
    try:
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        content = ""
        
        # Try different selectors based on website
        if 'vietstock.vn' in url:
            # VietStock content selectors
            article_body = soup.find('div', {'class': 'detail-content'}) or \
                          soup.find('div', {'class': 'content-news'}) or \
                          soup.find('div', {'class': 'article-content'})
        elif 'cafef.vn' in url:
            # CafeF content selectors
            article_body = soup.find('div', {'class': 'detail-content'}) or \
                          soup.find('div', {'class': 'content'}) or \
                          soup.find('div', {'id': 'ctl00_cphContent_divContent'})
        else:
            # Generic selectors
            article_body = soup.find('article') or \
                          soup.find('div', {'class': re.compile(r'content|article|body')})
        
        if article_body:
            # Extract text content
            paragraphs = article_body.find_all(['p', 'div'], text=True)
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Fallback: get all paragraph text
        if not content:
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Clean up content
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
        
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return ""

def parse_rss_feed(self, feed_url, source_name):
    """Parse RSS feed and extract articles"""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries[:10]:  # Limit to 10 latest articles
            try:
                # Get full content
                full_content = self.get_full_article_content(entry.link)
                
                # Parse published date
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6]).isoformat()
                elif hasattr(entry, 'published'):
                    try:
                        published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').isoformat()
                    except:
                        published_date = entry.published
                
                article = {
                    'id': f"{source_name}_{hash(entry.link)}",
                    'title': entry.title,
                    'link': entry.link,
                    'summary': getattr(entry, 'summary', ''),
                    'full_content': full_content,
                    'published_date': published_date,
                    'source': source_name,
                    'word_count': len(full_content.split()) if full_content else 0
                }
                
                articles.append(article)
                
            except Exception as e:
                logger.error(f"Error processing article {entry.link}: {e}")
                continue
                
        return articles
        
    except Exception as e:
        logger.error(f"Error parsing RSS feed {feed_url}: {e}")
        return []
```

class NewsChunker:
def **init**(self, chunk_size=1000):
self.chunk_size = chunk_size

```
def create_chunks(self, article):
    """Create chunks from article content"""
    if not article['full_content']:
        return []
    
    content = article['full_content']
    words = content.split()
    chunks = []
    
    for i in range(0, len(words), self.chunk_size):
        chunk_words = words[i:i + self.chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        chunk = {
            'chunk_id': f"{article['id']}_chunk_{i // self.chunk_size + 1}",
            'article_id': article['id'],
            'title': article['title'],
            'chunk_index': i // self.chunk_size + 1,
            'total_chunks': (len(words) + self.chunk_size - 1) // self.chunk_size,
            'content': chunk_text,
            'word_count': len(chunk_words),
            'source': article['source'],
            'link': article['link'],
            'published_date': article['published_date']
        }
        chunks.append(chunk)
    
    return chunks
```

# Initialize components

news_extractor = NewsExtractor()
news_chunker = NewsChunker(chunk_size=800)  # Adjust chunk size as needed

@app.route(’/’)
def home():
“”“API documentation”””
return jsonify({
‘message’: ‘Vietnamese Stock News API’,
‘endpoints’: {
‘/api/news’: ‘Get all news articles’,
‘/api/news/chunks’: ‘Get all news articles as chunks’,
‘/api/news/source/<source_name>’: ‘Get news from specific source’,
‘/api/news/source/<source_name>/chunks’: ‘Get chunks from specific source’,
‘/api/health’: ‘Health check’
},
‘available_sources’: list(RSS_FEEDS.keys())
})

@app.route(’/api/health’)
def health_check():
“”“Health check endpoint”””
return jsonify({‘status’: ‘healthy’, ‘timestamp’: datetime.now().isoformat()})

@app.route(’/api/news’)
def get_all_news():
“”“Get all news articles from all sources”””
try:
all_articles = []

```
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {
            executor.submit(news_extractor.parse_rss_feed, url, source): source
            for source, url in RSS_FEEDS.items()
        }
        
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error getting news from {source}: {e}")
    
    # Sort by published date (newest first)
    all_articles.sort(key=lambda x: x['published_date'] or '0', reverse=True)
    
    return jsonify({
        'total_articles': len(all_articles),
        'articles': all_articles,
        'timestamp': datetime.now().isoformat()
    })
    
except Exception as e:
    logger.error(f"Error in get_all_news: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

@app.route(’/api/news/chunks’)
def get_all_news_chunks():
“”“Get all news articles as chunks”””
try:
chunk_size = request.args.get(‘chunk_size’, 800, type=int)
chunker = NewsChunker(chunk_size=chunk_size)

```
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {
            executor.submit(news_extractor.parse_rss_feed, url, source): source
            for source, url in RSS_FEEDS.items()
        }
        
        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                articles = future.result()
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error getting news from {source}: {e}")
    
    # Create chunks for all articles
    all_chunks = []
    for article in all_articles:
        chunks = chunker.create_chunks(article)
        all_chunks.extend(chunks)
    
    # Sort chunks by published date (newest first)
    all_chunks.sort(key=lambda x: x['published_date'] or '0', reverse=True)
    
    return jsonify({
        'total_chunks': len(all_chunks),
        'total_articles': len(all_articles),
        'chunk_size': chunk_size,
        'chunks': all_chunks,
        'timestamp': datetime.now().isoformat()
    })
    
except Exception as e:
    logger.error(f"Error in get_all_news_chunks: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

@app.route(’/api/news/source/<source_name>’)
def get_news_by_source(source_name):
“”“Get news from specific source”””
if source_name not in RSS_FEEDS:
return jsonify({‘error’: ‘Source not found’}), 404

```
try:
    articles = news_extractor.parse_rss_feed(RSS_FEEDS[source_name], source_name)
    
    return jsonify({
        'source': source_name,
        'total_articles': len(articles),
        'articles': articles,
        'timestamp': datetime.now().isoformat()
    })
    
except Exception as e:
    logger.error(f"Error getting news from {source_name}: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

@app.route(’/api/news/source/<source_name>/chunks’)
def get_news_chunks_by_source(source_name):
“”“Get news chunks from specific source”””
if source_name not in RSS_FEEDS:
return jsonify({‘error’: ‘Source not found’}), 404

```
try:
    chunk_size = request.args.get('chunk_size', 800, type=int)
    chunker = NewsChunker(chunk_size=chunk_size)
    
    articles = news_extractor.parse_rss_feed(RSS_FEEDS[source_name], source_name)
    
    # Create chunks for all articles
    all_chunks = []
    for article in articles:
        chunks = chunker.create_chunks(article)
        all_chunks.extend(chunks)
    
    return jsonify({
        'source': source_name,
        'total_chunks': len(all_chunks),
        'total_articles': len(articles),
        'chunk_size': chunk_size,
        'chunks': all_chunks,
        'timestamp': datetime.now().isoformat()
    })
    
except Exception as e:
    logger.error(f"Error getting chunks from {source_name}: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

if **name** == ‘**main**’:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port, debug=False)