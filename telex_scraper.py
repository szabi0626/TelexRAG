# telex_scraper.py
import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict


class TelexScraper:
    BASE_URL = "https://telex.hu"
    ARCHIVE_RSS_URL = f"{BASE_URL}/rss/archivum"

    @staticmethod
    def search_articles(query: Dict = None, max_results: int = 5) -> List[Dict]:
        """
        Fetch articles from Telex archive RSS feed, going through multiple pages if necessary.
        """
        filters = {"and_tags": [], "superTags": [], "authors": [], "title": []}

        filters_encoded = urllib.parse.quote(json.dumps(filters, ensure_ascii=False))
        # Handle query parameter correctly based on type
        term = ""
        if isinstance(query, dict) and "query" in query:
            term = query["query"]
        else:
            # Convert query to string if it's not already
            query_str = str(query)

            # Check if the string follows the pattern query="something"
            import re

            match = re.search(r'query=["\']([^"\']+)["\']', query_str)
            if match:
                # Extract the term inside the quotes
                term = match.group(1)
            else:
                # Use the whole string as the term
                term = query_str
        if term == "None":
            term = ""

        term = term.replace(" ", "%20")

        articles = []
        page = 1
        per_page = 10  # how many articles to request per page

        while len(articles) < max_results:
            rss_url = f"{TelexScraper.ARCHIVE_RSS_URL}?filters={filters_encoded}&perPage={per_page}&oldal={page}&term={term}"
            # print(f"Fetching page {page}: {rss_url}")

            response = requests.get(rss_url)
            if response.status_code != 200:
                print(
                    f"Failed to fetch page {page}. Status code: {response.status_code}"
                )
                break

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")

            if not items:
                print("No more articles found.")
                break

            for item in items:
                if len(articles) >= max_results:
                    break

                title = item.find("title").text
                link = item.find("link").text
                pub_date = (
                    item.find("pubDate").text
                    if item.find("pubDate")
                    else "Unknown Date"
                )

                articles.append({"title": title, "url": link, "date": pub_date})

            page += 1  # Move to next page

        return articles

    @staticmethod
    def scrape_article_content(url: str) -> Dict:
        """
        Scrape a single article page for title, lead, and full content.
        """
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch article: {url}")
            return {"title": "Unknown Title", "url": url, "content": ""}

        soup = BeautifulSoup(response.content, "html.parser")

        title_tag = soup.select_one(
            "#cikk-content > div.title-section > div.title-section__top > h1"
        )
        lead_tag = soup.select_one(
            "#cikk-content > div.article_body_ > div.article_container_.article-box-margin > p"
        )
        body_tag = soup.select_one(
            "#cikk-content > div.article_body_ > div.article_container_.article-box-margin > div.article-html-content"
        )

        title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
        lead = lead_tag.get_text(strip=True) if lead_tag else ""
        body = body_tag.get_text(strip=True) if body_tag else ""

        content = f"{lead}\n\n{body}" if lead else body

        return {"title": title, "url": url, "content": content}
