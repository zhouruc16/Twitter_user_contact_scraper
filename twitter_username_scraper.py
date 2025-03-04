import re
import csv
import time
import datetime
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class TwitterScraper:
    def __init__(
        self,
        driver_path,
        csv_file,
        search_query,
        wait_login=30,
        headless=False,
        user_data_dir=None,
        profile_directory=None,
    ):
        self.driver_path = driver_path
        self.csv_file = csv_file
        self.search_query = search_query
        self.wait_login = wait_login
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory
        self.processed_tweets = set()
        self.driver = self.init_driver()
        self.csv_writer, self.csv_handle = self.init_csv()

    def init_driver(self):
        chrome_options = Options()
        # Enable headless mode if required
        if self.headless:
            chrome_options.add_argument("--headless")
        # Additional options to reduce detection risk
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.0.0 Safari/537.36"
        )
        # Add user data directory and profile if provided
        if self.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        if self.profile_directory:
            chrome_options.add_argument(f"--profile-directory={self.profile_directory}")

        service = Service(self.driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def init_csv(self):
        fieldnames = ["handle", "email", "phone", "instagram", "whatsapp"]
        csv_handle = open(self.csv_file, mode="w", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_handle, fieldnames=fieldnames)
        writer.writeheader()
        csv_handle.flush()
        return writer, csv_handle

    def login(self):
        self.driver.get("https://twitter.com/login")
        print(f"Please log in to Twitter manually if necessary. Waiting {self.wait_login} seconds...")
        time.sleep(self.wait_login)

    def search(self):
        # If the search query starts with a hashtag, URL-encode the '#' as '%23'
        if self.search_query.startswith("#"):
            query = self.search_query.replace("#", "%23", 1)
        else:
            query = self.search_query
        search_url = f"https://twitter.com/search?q={query}&src=typed_query"
        self.driver.get(search_url)
        time.sleep(5)

    def scroll_page(self, pause=3, max_attempts=5):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        attempts = 0
        while attempts < max_attempts:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            attempts += 1

    def collect_tweet_urls(self):
        tweet_elements = self.driver.find_elements(By.XPATH, '//article')
        new_tweet_urls = []
        for tweet in tweet_elements:
            try:
                link_element = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                tweet_url = link_element.get_attribute("href")
                if tweet_url not in self.processed_tweets:
                    new_tweet_urls.append(tweet_url)
            except Exception:
                continue
        return list(set(new_tweet_urls))

    def extract_handles_from_tweet(self):
        handles = set()
        # Extract the tweet poster's handle
        try:
            original_handle = self.driver.find_element(
                By.XPATH, '//article//div[@data-testid="User-Name"]//span[contains(text(),"@")]'
            ).text.strip()
            handles.add(original_handle)
            print("Tweet poster:", original_handle)
        except Exception as e:
            print("Error extracting tweet poster handle:", e)
        # Extract additional handles from comments/articles
        articles = self.driver.find_elements(By.XPATH, '//article')
        for art in articles:
            try:
                handle = art.find_element(
                    By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(),"@")]'
                ).text.strip()
                if handle:
                    handles.add(handle)
            except Exception:
                continue
        print("Handles found:", handles)
        return handles

    def process_tweet(self, tweet_url):
        print(f"\nProcessing tweet: {tweet_url}")
        self.processed_tweets.add(tweet_url)
        # Open tweet detail page in a new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(tweet_url)
        time.sleep(5)
        # Scroll down to load all comments
        self.scroll_page(pause=3)
        # Extract handles from tweet details
        handles = self.extract_handles_from_tweet()
        # For each handle, use ProfileScraper to scrape contact info
        profile_scraper = ProfileScraper(self.driver)
        for handle in handles:
            contact_info = profile_scraper.scrape_profile_contact_info(handle)
            print("Contact info for", handle, ":", contact_info)
            self.csv_writer.writerow(contact_info)
            self.csv_handle.flush()
        # Close tweet detail tab and return to main search results tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def run(self):
        self.login()
        self.search()
        while True:
            new_tweet_urls = self.collect_tweet_urls()
            print(f"Found {len(new_tweet_urls)} new tweets to process.")
            if not new_tweet_urls:
                self.scroll_page(pause=5)
                new_tweet_urls = self.collect_tweet_urls()
                if not new_tweet_urls:
                    print("No new tweets found. Exiting loop.")
                    break
            for tweet_url in new_tweet_urls:
                self.process_tweet(tweet_url)
            self.scroll_page(pause=5)
        self.driver.quit()
        self.csv_handle.close()
        print(f"Scraped user info saved to {self.csv_file}")


class ProfileScraper:
    def __init__(self, driver):
        self.driver = driver
        self.email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        self.phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
        self.instagram_pattern = re.compile(r'https?://(?:www\.)?instagram\.com/[\w_.]+')
        self.whatsapp_pattern = re.compile(r'https?://(?:wa\.me|api\.whatsapp\.com/send)\S+')

    def scrape_profile_contact_info(self, handle):
        contact_info = {
            "handle": handle,
            "email": None,
            "phone": None,
            "instagram": None,
            "whatsapp": None
        }
        username = handle.lstrip('@')
        profile_url = f"https://twitter.com/{username}"
        print(f"Scraping profile: {profile_url}")
        # Open the profile page in a new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(profile_url)
        time.sleep(5)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        try:
            profile_box = self.driver.find_element(By.XPATH, '//div[@data-testid="UserProfileHeader_Items"]')
            page_text = profile_box.text
        except Exception:
            print("Profile box not found for", handle)
            page_text = ""
        emails = self.email_pattern.findall(page_text)
        if emails:
            contact_info["email"] = emails[0]
        phones = self.phone_pattern.findall(page_text)
