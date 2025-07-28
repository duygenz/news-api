# app.py

import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Danh sách các nguồn RSS
RSS_FEEDS = [
    "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://vietstock.vn/145/chung-khoan/y-kien-chuyen-gia.rss",
    "https://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
    "https://vietstock.vn/1328/dong-duong/thi-truong-chung-khoan.rss",
]

# Hàm để lấy nội dung đầy đủ của bài viết
def get_full_article(url):
    """
    Truy cập URL của bài viết và trích xuất toàn bộ nội dung.
    Hàm này cần được tùy chỉnh cho từng trang web khác nhau.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Ném lỗi nếu request không thành công
        soup = BeautifulSoup(response.content, "html.parser")

        # Logic cho Vietstock
        if "vietstock.vn" in url:
            # Vietstock dùng div có id 'vst-content' cho nội dung chính
            content_div = soup.find("div", {"id": "vst-content"})
            if content_div:
                return content_div.get_text(separator="\n", strip=True)

        # Logic cho Cafef
        elif "cafef.vn" in url:
            # Cafef dùng div có id 'main-content'
            content_div = soup.find("div", {"class": "content-detail"})
            if content_div:
                return content_div.get_text(separator="\n", strip=True)

        return "Không thể lấy được nội dung."

    except requests.RequestException as e:
        print(f"Lỗi khi truy cập {url}: {e}")
        return "Lỗi khi truy cập URL."
    except Exception as e:
        print(f"Lỗi không xác định với {url}: {e}")
        return "Lỗi không xác định."

# Hàm để xử lý một RSS feed
def process_feed(feed_url):
    """
    Phân tích một RSS feed và lấy thông tin các bài viết.
    """
    news_list = []
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        news_list.append(
            {
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "N/A"),
                "summary": entry.summary,
            }
        )
    return news_list

# API endpoint chính
@app.route("/news")
def get_news_in_chunks():
    """
    Lấy tin tức từ tất cả các nguồn RSS và trả về dưới dạng JSON.
    Sử dụng multi-threading để tăng tốc độ lấy tin.
    """
    all_articles_metadata = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Lấy danh sách các bài viết từ tất cả các feed
        results = executor.map(process_feed, RSS_FEEDS)
        for news_list in results:
            all_articles_metadata.extend(news_list)

    # Lấy nội dung đầy đủ cho từng bài viết
    def fetch_full_content(article):
        article["full_content"] = get_full_article(article["link"])
        return article

    # Sử dụng multi-threading để lấy nội dung đầy đủ
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Giới hạn số lượng bài viết để tránh quá tải
        full_articles = list(executor.map(fetch_full_content, all_articles_metadata[:20]))

    return jsonify(full_articles)

# Chạy ứng dụng
if __name__ == "__main__":
    # Chạy trên cổng 8080 hoặc cổng do Render cung cấp
    app.run(host="0.0.0.0", port=8080)
