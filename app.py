from flask import Flask, jsonify
from flask_cors import CORS
import feedparser
import threading
from time import time

# --- Configuration ---
RSS_FEEDS = [
    'https://cafef.vn/thi-truong-chung-khoan.rss',
    'https://vneconomy.vn/chung-khoan.rss',
    'https://vneconomy.vn/tai-chinh.rss',
    'https://vneconomy.vn/thi-truong.rss',
    'https://vneconomy.vn/nhip-cau-doanh-nghiep.rss',
    'https://vneconomy.vn/tin-moi.rss',
    'https://cafebiz.vn/rss/cau-chuyen-kinh-doanh.rss'
]

# --- Flask App Initialization ---
app = Flask(__name__)
# This enables CORS for all domains on all routes.
CORS(app)

# --- In-Memory Caching ---
# A simple cache to store the news and avoid re-fetching on every request.
news_cache = {
    "articles": [],
    "last_updated": 0
}
CACHE_DURATION_SECONDS = 600  # Cache news for 10 minutes

# --- Core Logic ---
def fetch_single_feed(url, articles_list):
    """Fetches entries from a single RSS feed and appends them to a list."""
    try:
        feed = feedparser.parse(url)
        source_name = feed.feed.get('title', 'Unknown Source')
        for entry in feed.entries:
            articles_list.append({
                'source': source_name,
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', '#'),
                'published': entry.get('published', 'No Date'),
                'summary': entry.get('summary', 'No Summary')
            })
    except Exception as e:
        print(f"Error fetching feed {url}: {e}")

def update_news_cache():
    """
    Fetches all RSS feeds concurrently using threads and updates the cache.
    """
    global news_cache
    print("Updating news cache...")
    articles = []
    threads = []

    for url in RSS_FEEDS:
        thread = threading.Thread(target=fetch_single_feed, args=(url, articles))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
    
    # Sort articles by published date (best effort)
    # Note: Date formats can be inconsistent across feeds.
    try:
        articles.sort(key=lambda x: feedparser._parse_date(x['published']), reverse=True)
    except Exception:
        # If dates can't be parsed, just leave the order as is.
        pass

    news_cache['articles'] = articles
    news_cache['last_updated'] = time()
    print(f"Cache updated with {len(articles)} articles.")


# --- API Endpoint ---
@app.route('/news', methods=['GET'])
def get_news():
    """
    The main API endpoint. It returns cached news or triggers a fetch if the
    cache is stale.
    """
    is_cache_stale = (time() - news_cache['last_updated']) > CACHE_DURATION_SECONDS
    if not news_cache['articles'] or is_cache_stale:
        update_news_cache()
    
    return jsonify(news_cache['articles'])

@app.route('/', methods=['GET'])
def index():
    """A simple welcome message for the root URL."""
    return "<h1>News Aggregator API</h1><p>Use the <code>/news</code> endpoint to get the latest articles.</p>"

# This is necessary for Render's deployment environment.
if __name__ == '__main__':
    # Initial data fetch on startup
    update_news_cache()
    # The app is run by Gunicorn in production, not this command.
    app.run(host='0.0.0.0', port=5001)

