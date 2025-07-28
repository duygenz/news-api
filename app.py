from flask import Flask, jsonify
import asyncio
import aiohttp
from news_fetcher import async_fetch_feed

app = Flask(__name__)

RSS_FEEDS = [
    "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://vietstock.vn/145/chung-khoan/y-kien-chuyen-gia.rss",
    "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
    "https://vietstock.vn/1328/dong-duong/thi-truong-chung-khoan.rss"
]

async def fetch_all_news():
    async with aiohttp.ClientSession() as session:
        tasks = [async_fetch_feed(session, url) for url in RSS_FEEDS]
        results = await asyncio.gather(*tasks)
        
        all_news = []
        for news in results:
            all_news.extend(news)
        return all_news

@app.route('/news', methods=['GET'])
def get_news():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    news = loop.run_until_complete(fetch_all_news())
    loop.close()
    
    return jsonify({
        "total_articles": len(news),
        "results": news
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)