import requests
from bs4 import BeautifulSoup
import csv
import time
import logging
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth

# Try to import Selenium components
try:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        webdriver = Service = By = Options = None
        print("Selenium is not installed. Please install it with 'pip install selenium'.")
except ImportError:
    webdriver = None
    Service = None
    By = None
    Options = None
    import sys
    logging.error("Selenium is not installed. Please install it with 'pip install selenium' to use JS rendering.")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("web_scraper.log"),
        logging.StreamHandler()
    ]
)

# Helper function for JavaScript rendering
def render_page_js(url, headless=True, driver_path=None):
    """Renders a webpage using Selenium with JavaScript support."""
    if webdriver is None or Options is None or Service is None:
        raise ImportError("Selenium and Chrome WebDriver are required for JS rendering.")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(executable_path=driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logging.info(f"Rendering JavaScript for URL: {url} (headless={headless})")
    driver.get(url)
    time.sleep(3)  # Allow time for rendering, tweak as needed
    page_source = driver.page_source
    driver.quit()
    return page_source

def scrape_website(
    base_url,
    output_file,
    max_pages=1,
    rate_limit=2,
    user_agent="Mozilla/5.0",
    auth=None,
    render_js=False,
    driver_path=None,
    extract_method=None,
    extraction_params=None
):
    """
    Scrapes a website and extracts data flexibly using the given extraction method.
    Parameters:
        - base_url: The starting URL of the website.
        - output_file: CSV file to save the results.
        - max_pages: Maximum number of pages to scrape.
        - rate_limit: Pause duration (in seconds) between requests.
        - user_agent: Custom User-Agent string for requests.
        - auth: Tuple with (username, password) for basic authentication.
        - render_js: Whether to render JavaScript using Selenium.
        - driver_path: Path to the Chrome WebDriver.
        - extract_method: Custom function for extraction.
        - extraction_params: Parameters for the custom extraction function.
    """
    headers = {"User-Agent": user_agent}
    scraped_data = []

    for page in range(1, max_pages + 1):
        page_url = urljoin(base_url, f"?page={page}")  # Update URL construction logic if needed
        logging.info(f"Scraping page {page}: {page_url}")

        # Get raw or rendered content
        if render_js:
            html = render_page_js(page_url, headless=True, driver_path=driver_path)
        else:
            response = requests.get(page_url, headers=headers, auth=auth)
            if response.status_code != 200:
                logging.error(f"Failed to retrieve {page_url}: {response.status_code}")
                break
            html = response.text

        # Extract content
        if extract_method is not None and callable(extract_method):
            try:
                data = extract_method(html, extraction_params)
                # Ensure data is iterable (list/tuple), else wrap in list
                if not hasattr(data, "__iter__") or isinstance(data, (str, bytes)):
                    data = [data]
                if isinstance(data, list):
                    scraped_data.extend(data)
                else:
                    scraped_data.append(data)
                try:
                    logging.info(f"Extracted {len(data)} items from page {page}.")
                except TypeError:
                    logging.info(f"Extracted 1 item from page {page}.")
            except Exception as e:
                logging.error(f"Error during extraction on page {page}: {str(e)}")
                continue
        else:
            logging.warning("No valid extraction method specified. Skipping data extraction.")
            continue

        # Respect rate limit
        time.sleep(rate_limit)

    # Save to CSV
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            if scraped_data:
                # Write headers dynamically based on keys in the first row of data
                csv_writer.writerow(scraped_data[0].keys())
                for row in scraped_data:
                    csv_writer.writerow(row.values())
        logging.info(f"Scraped data saved to {output_file}")
    except Exception as e:
        logging.error(f"Failed to save to CSV: {str(e)}")

    logging.info("Scraping complete.")

# Example extraction method (can be replaced with custom logic)
def example_extract_method(html, params):
    """Example extraction method using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    data = []
    for item in soup.select(params.get("selector", "div.item")):  # Use 'selector' parameter
        title = item.select_one(params.get("title_selector", "h2.title"))
        description = item.select_one(params.get("desc_selector", "p.description"))
        data.append({
            "title": title.text.strip() if title else "N/A",
            "description": description.text.strip() if description else "N/A"
        })
    return data

# Usage example
if __name__ == "__main__":
    base_url = "https://example.com/listings"
    output_file = "scraped_results.csv"
    custom_extraction_params = {
        "selector": "div.listing",
        "title_selector": "h2.name",
        "desc_selector": "p.summary"
    }
    scrape_website(
        base_url=base_url,
        output_file=output_file,
        max_pages=5,
        rate_limit=1,
        user_agent="Mozilla/5.0 (compatible; CustomBot/1.0)",
        render_js=True,
        driver_path="/path/to/chromedriver",  # Specify your Chromedriver path here
        extract_method=example_extract_method,
        extraction_params=custom_extraction_params
    )
