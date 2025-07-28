from flask import Flask, jsonify
from news_fetcher import get_news_from_rss

app = Flask(__name__)

RSS_FEEDS = [
    "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://vietstock.vn/145/chung-khoan/y-kien-chuyen-gia.rss",
    "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
    "https://vietstock.vn/1328/dong-duong/thi-truong-chung-khoan.rss"
]

@app.route('/news', methods=['GET'])
def get_news():
    all_news = []
    for rss_url in RSS_FEEDS:
        try:
            news = get_news_from_rss(rss_url)
            all_news.extend(news)
        except Exception as e:
            print(f"Error processing {rss_url}: {e}")
    
    return jsonify({
        "total_articles": len(all_news),
        "results": all_news
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
