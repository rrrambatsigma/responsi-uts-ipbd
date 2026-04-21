import csv
import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JSON_PATH = DATA_DIR / "wired_articles.json"
CSV_PATH = DATA_DIR / "wired_articles.csv"

TARGET_MIN_ARTICLES = 150

SOURCE_PAGES = [
    "https://www.wired.com",
    "https://www.wired.com/category/business/",
    "https://www.wired.com/category/security/",
    "https://www.wired.com/category/politics/",
    "https://www.wired.com/category/science/",
    "https://www.wired.com/category/culture/",
    "https://www.wired.com/category/gear/",
    "https://www.wired.com/category/ideas/",
]


def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless=new")  # aktifkan kalau sudah stabil

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def scroll_page(driver, times=12, pause=2):
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"[INFO] Scroll ke-{i + 1}")
        time.sleep(pause)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            continue
        last_height = new_height


def collect_article_links_from_page(driver, page_url):
    seen_urls = set()

    print(f"\n[INFO] Membuka source page: {page_url}")
    driver.get(page_url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
    )

    print("[INFO] Mulai scroll halaman sumber...")
    scroll_page(driver, times=12, pause=2)

    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"[INFO] Total link mentah ditemukan di halaman ini: {len(links)}")

    for link in links:
        try:
            url = link.get_attribute("href")

            if not url:
                continue

            url = url.strip()

            if "wired.com/story/" not in url:
                continue

            seen_urls.add(url)

        except Exception:
            continue

    print(f"[INFO] URL artikel unik dari halaman ini: {len(seen_urls)}")
    return seen_urls


def collect_article_links(driver, target_count=150):
    all_urls = set()

    for page_url in SOURCE_PAGES:
        page_urls = collect_article_links_from_page(driver, page_url)
        all_urls.update(page_urls)

        print(f"[INFO] Total URL artikel unik terkumpul saat ini: {len(all_urls)}")

        if len(all_urls) >= target_count:
            print(f"[INFO] Target minimal {target_count} URL artikel sudah tercapai.")
            break

    article_urls = list(all_urls)
    print(f"[INFO] Final total URL artikel unik: {len(article_urls)}")
    return article_urls


def safe_find_text(driver, selectors):
    for by, value in selectors:
        try:
            element = driver.find_element(by, value)
            text = element.text.strip()
            if text:
                return text
        except NoSuchElementException:
            continue
        except Exception:
            continue
    return None


def scrape_article_detail(driver, url):
    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(2)

        title = safe_find_text(driver, [
            (By.TAG_NAME, "h1"),
            (By.CSS_SELECTOR, "main h1"),
            (By.CSS_SELECTOR, "article h1"),
        ])

        description = None
        try:
            meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            description = meta_desc.get_attribute("content")
            if description:
                description = description.strip()
        except Exception:
            description = safe_find_text(driver, [
                (By.CSS_SELECTOR, "main p"),
                (By.CSS_SELECTOR, "article p"),
            ])

        author = safe_find_text(driver, [
            (By.CSS_SELECTOR, '[data-testid="Byline"]'),
            (By.CSS_SELECTOR, '[class*="byline"]'),
            (By.CSS_SELECTOR, 'a[rel="author"]'),
            (By.XPATH, "//*[contains(text(),'By ')]"),
        ])

        if not author:
            try:
                possible_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'By ')]")
                for el in possible_elements:
                    txt = el.text.strip()
                    if txt and len(txt) < 120:
                        author = txt
                        break
            except Exception:
                author = None

        article = {
            "title": title,
            "url": url,
            "description": description,
            "author": author,
            "scraped_at": datetime.now().isoformat(),
            "source": "Wired.com"
        }

        return article

    except TimeoutException:
        print(f"[WARNING] Timeout saat buka artikel: {url}")
        return None
    except Exception as e:
        print(f"[WARNING] Gagal scrape detail artikel: {url} | Error: {e}")
        return None


def clean_articles(articles):
    cleaned = []
    seen = set()

    for article in articles:
        if not article:
            continue

        title = article.get("title")
        url = article.get("url")

        if not title or not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        cleaned.append(article)

    return cleaned


def save_to_json(data, path):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload = [
        {
            "session_id": f"wired_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "articles_count": len(data),
            "articles": data
        }
    ]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    print(f"[INFO] JSON berhasil disimpan: {path}")


def save_to_csv(data, path):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = ["title", "url", "description", "author", "scraped_at", "source"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"[INFO] CSV berhasil disimpan: {path}")


def main():
    driver = setup_driver()

    try:
        print("[INFO] Mulai mengumpulkan URL artikel Wired...")
        article_urls = collect_article_links(driver, target_count=TARGET_MIN_ARTICLES)

        if len(article_urls) < TARGET_MIN_ARTICLES:
            print(
                f"[WARNING] URL artikel yang ditemukan baru {len(article_urls)}. "
                f"Target {TARGET_MIN_ARTICLES} belum tercapai, tapi scrape detail tetap dijalankan."
            )

        target_urls = article_urls[:TARGET_MIN_ARTICLES]

        scraped_articles = []

        for idx, url in enumerate(target_urls, start=1):
            print(f"[INFO] Scrape artikel ke-{idx}/{len(target_urls)}: {url}")
            article = scrape_article_detail(driver, url)

            if article:
                scraped_articles.append(article)

        cleaned_articles = clean_articles(scraped_articles)

        print(f"[INFO] Total artikel valid setelah cleaning: {len(cleaned_articles)}")

        save_to_json(cleaned_articles, JSON_PATH)
        save_to_csv(cleaned_articles, CSV_PATH)

        print("\n=== SAMPLE DATA ===")
        for i, item in enumerate(cleaned_articles[:5], start=1):
            print(f"\nArtikel {i}")
            print("Title      :", item.get("title"))
            print("URL        :", item.get("url"))
            print("Description:", item.get("description"))
            print("Author     :", item.get("author"))
            print("Scraped At :", item.get("scraped_at"))
            print("Source     :", item.get("source"))

    finally:
        driver.quit()


if __name__ == "__main__":
    main()