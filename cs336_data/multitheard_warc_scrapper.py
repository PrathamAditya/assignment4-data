import concurrent.futures
from io import BytesIO
import threading
import requests
from requests.adapters import HTTPAdapter
from warcio.statusandheaders import StatusAndHeaders
from warcio.warcwriter import WARCWriter

TIMEOUT = (3.0, 5.0)  # (connect_timeout, read_timeout)
MAX_WORKERS = 48
INPUT_FILE = "data/subsampled_positive_urls.txt"
OUTPUT_WARC_FILE = "data/subsampled_positive_urls_2.warc.gz"

write_lock = threading.Lock()

session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=MAX_WORKERS,
    pool_maxsize=MAX_WORKERS,
    max_retries=0,
)
session.mount("http://", adapter)
session.mount("https://", adapter)


def fetch_url(url: str):
    """Fetches a URL using the pooled session."""
    try:
        # 2. Use session.get instead of requests.get
        resp = session.get(
            url,
            timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CS336Scraper/1.0)"},
            allow_redirects=True,
            stream=False,
        )
        return url, resp
    except Exception:
        return url, None


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Starting scrape for {len(urls)} URLs across {MAX_WORKERS} threads...")

    success_count = 0

    with open(OUTPUT_WARC_FILE, "wb") as warc_out:
        writer = WARCWriter(warc_out, gzip=True)

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(fetch_url, url): url for url in urls}

            for future in concurrent.futures.as_completed(future_to_url):
                url, resp = future.result()

                if resp is not None and resp.status_code == 200:
                    status_line = f"{resp.status_code} {resp.reason or 'OK'}".strip()
                    http_headers = StatusAndHeaders(
                        status_line,
                        list(resp.headers.items()),
                        protocol="HTTP/1.1",
                    )

                    record = writer.create_warc_record(
                        uri=url,
                        record_type="response",
                        payload=BytesIO(resp.content),
                        http_headers=http_headers,
                    )

                    with write_lock:
                        writer.write_record(record)

                    success_count += 1

    print(f"Scrape completed. Saved {success_count}/{len(urls)} records into '{OUTPUT_WARC_FILE}'.")


if __name__ == "__main__":
    main()