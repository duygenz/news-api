import asyncio
import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import feedparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="Vietnamese News API",
    description="API tổng hợp, trích xuất và chia nhỏ nội dung tin tức từ các trang báo Việt Nam.",
    version="1.0.0"
)

# Cấu hình CORS (Cross-Origin Resource Sharing)
# Cho phép tất cả các nguồn gốc (origins) truy cập API.
# Trong môi trường production, bạn nên giới hạn lại chỉ những domain được phép.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (GET, POST, etc.)
    allow_headers=["*"],  # Cho phép tất cả các headers
)

# Danh sách các nguồn RSS feed
RSS_FEEDS = [
    "https://cafef.vn/thi-truong-chung-khoan.rss",
    "https://vneconomy.vn/chung-khoan.rss",
    "https://vneconomy.vn/tai-chinh.rss",
    "https://vneconomy.vn/thi-truong.rss",
    "https://vneconomy.vn/nhip-cau-doanh-nghiep.rss",
    "https://vneconomy.vn/tin-moi.rss",
    "https://cafebiz.vn/rss/cau-chuyen-kinh-doanh.rss"
]

# --- Helper Functions ---

def get_full_content_from_url(url: str) -> str:
    """
    Truy cập một URL bài báo và trích xuất nội dung văn bản đầy đủ.
    Lưu ý: Cấu trúc selector có thể cần được cập nhật nếu trang web thay đổi layout.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Logic để tìm nội dung chính dựa trên cấu trúc HTML của từng trang
        content = ""
        if "vneconomy.vn" in url:
            article_body = soup.find("div", class_="detail__content")
            if article_body:
                content = article_body.get_text(separator="\n", strip=True)
        elif "cafef.vn" in url or "cafebiz.vn" in url:
            article_body = soup.find("div", id="mainContent")
            if article_body:
                content = article_body.get_text(separator="\n", strip=True)
        else:
            # Một selector chung chung hơn nếu không khớp
            article_body = soup.find("article") or soup.find("div", class_="content")
            if article_body:
                content = article_body.get_text(separator="\n", strip=True)

        # Dọn dẹp văn bản
        content = re.sub(r'\s*\n\s*', '\n', content).strip()
        return content

    except requests.RequestException as e:
        print(f"Lỗi khi lấy nội dung từ {url}: {e}")
        return ""
    except Exception as e:
        print(f"Lỗi không xác định khi xử lý {url}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> List[str]:
    """
    Chia một đoạn văn bản dài thành các đoạn nhỏ hơn (chunks) có kích thước xấp xỉ `chunk_size`
    và có sự chồng lấp (overlap) giữa các chunk.
    """
    if not text:
        return []
    
    # Chia văn bản thành các câu để tránh cắt giữa câu
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 > chunk_size:
            chunks.append(current_chunk.strip())
            # Bắt đầu chunk mới với một phần overlap từ chunk cũ
            start_index = max(0, len(current_chunk) - overlap)
            current_chunk = current_chunk[start_index:] + " " + sentence
        else:
            current_chunk += " " + sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks


async def fetch_and_process_feed(feed_url: str) -> List[Dict[str, Any]]:
    """
    Lấy tin từ một RSS feed, trích xuất nội dung đầy đủ và chia nhỏ nội dung.
    Đây là một hàm bất đồng bộ (async).
    """
    print(f"Đang xử lý feed: {feed_url}")
    parsed_feed = feedparser.parse(feed_url)
    articles = []

    for entry in parsed_feed.entries:
        full_content = get_full_content_from_url(entry.link)
        if full_content:
            content_chunks = chunk_text(full_content)
            
            articles.append({
                "source": parsed_feed.feed.get("title", "Không rõ nguồn"),
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "Không rõ ngày"),
                "summary": entry.get("summary", ""),
                "full_content_chunks": content_chunks
            })
    return articles

# --- API Endpoints ---

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Chào mừng đến với API Tin tức Việt Nam. Truy cập /docs để xem tài liệu API."}


@app.get("/api/news", summary="Lấy tin tức hàng loạt từ tất cả các nguồn")
async def get_all_news():
    """
    Tổng hợp tin tức từ tất cả các RSS feed đã được định cấu hình.

    - **Lấy đồng thời**: API sẽ gọi đến tất cả các nguồn RSS cùng một lúc để tăng tốc độ.
    - **Lấy nội dung đầy đủ**: Hệ thống sẽ tự động truy cập link của từng bài báo để lấy toàn bộ nội dung.
    - **Tạo chunks**: Nội dung đầy đủ sẽ được chia thành các đoạn nhỏ hơn (chunks) để dễ dàng xử lý.
    """
    # Sử dụng asyncio.gather để chạy tất cả các tác vụ lấy feed đồng thời
    tasks = [fetch_and_process_feed(url) for url in RSS_FEEDS]
    results = await asyncio.gather(*tasks)
    
    # Làm phẳng danh sách kết quả (vì mỗi tác vụ trả về một danh sách)
    all_articles = [article for feed_result in results for article in feed_result]
    
    return {"count": len(all_articles), "articles": all_articles}

# Lệnh để chạy local: uvicorn main:app --reload
