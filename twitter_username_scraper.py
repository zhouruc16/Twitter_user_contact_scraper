import re
import csv
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class TwitterScraper:
    def __init__(
        self,
        csv_file,
        search_query,
        max_users,
        wait_login=30,
        headless=False,
        user_data_dir=None,
        profile_directory=None,
        driver_path=None
    ):
        self.driver_path = driver_path
        self.csv_file = csv_file
        self.search_query = search_query
        self.max_users = max_users
        self.user_count = 0
        self.wait_login = wait_login
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.profile_directory = profile_directory

        # We track processed tweets and users only by their handles to avoid duplicates
        self.processed_tweets = set()
        self.processed_users = set()

        self.driver = self.init_driver()
        self.csv_writer, self.csv_handle = self.init_csv()

    def init_driver(self):
        """Initialize the Chrome WebDriver with some stealth options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.0.0 Safari/537.36"
        )
        if self.user_data_dir:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        if self.profile_directory:
            chrome_options.add_argument(f"--profile-directory={self.profile_directory}")

        service = Service(ChromeDriverManager().install())
        if self.driver_path:
            service = Service(self.driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def init_csv(self):
        """Open or create the CSV file and write the header."""
        fieldnames = ["handle", "email", "phone", "instagram", "whatsapp"]
        csv_handle = open(self.csv_file, mode="w", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_handle, fieldnames=fieldnames)
        writer.writeheader()
        csv_handle.flush()  # Ensure header is saved immediately
        return writer, csv_handle

    def login(self):
        """Prompts for manual login, if no user profile is loaded."""
        self.driver.get("https://twitter.com/login")
        print(f"Please log in to Twitter manually if necessary. Waiting {self.wait_login} seconds...")
        time.sleep(self.wait_login)

    def search(self):
        """Go to the Twitter search page for the chosen query."""
        if self.search_query.startswith("#"):
            query = self.search_query.replace("#", "%23", 1)
        else:
            query = self.search_query
        search_url = f"https://twitter.com/search?q={query}&src=typed_query"
        self.driver.get(search_url)
        time.sleep(5)

    def scroll_page(self, pause=3, max_attempts=5):
        """Scroll the page multiple times to load tweets."""
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
        """Collect unique tweet URLs from the current page."""
        tweet_elements = self.driver.find_elements(By.XPATH, '//article')
        new_tweet_urls = []
        for tweet in tweet_elements:
            try:
                link_element = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                tweet_url = link_element.get_attribute("href")
                if tweet_url not in self.processed_tweets:
                    new_tweet_urls.append(tweet_url)
            except Exception:
                pass
        return list(set(new_tweet_urls))

    def extract_handles_from_tweet(self):
        """
        Extract the tweet poster's handle and any handles from replies in that tweet details page.
        We return them as a set to avoid duplicates.
        """
        handles = set()
        try:
            link_element = self.driver.find_element(
                By.XPATH, '//article//div[@data-testid="User-Name"]//a[starts-with(@href, "/")]'
            )
            original_url = link_element.get_attribute("href").strip()
            original_handle = '@' + original_url.rstrip("/").split("/")[-1]
            handles.add(original_handle)
            print("Tweet poster:", original_handle)
        except Exception as e:
            print("Error extracting tweet poster handle:", e)

        # Additional handles from replies
        articles = self.driver.find_elements(By.XPATH, '//article')
        for art in articles:
            try:
                link_element = art.find_element(
                    By.XPATH, './/div[@data-testid="User-Name"]//a[starts-with(@href, "/")]'
                )
                url = link_element.get_attribute("href").strip()
                handle = '@' + url.rstrip("/").split("/")[-1]
                if handle:
                    handles.add(handle)
            except Exception:
                pass
        print("Handles found:", handles)
        return handles

    def process_tweet(self, tweet_url):
        """Open tweet in new tab, get handles, scrape them, write to CSV one by one."""
        print(f"\nProcessing tweet: {tweet_url}")
        self.processed_tweets.add(tweet_url)

        # Open tweet detail in new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(tweet_url)
        time.sleep(5)
        self.scroll_page(pause=3)

        # Extract handles
        handles = self.extract_handles_from_tweet()

        # For each handle, scrape contact info and write to CSV
        profile_scraper = ProfileScraper(self.driver)
        for handle in handles:
            # If we've reached the limit, stop
            if self.user_count >= self.max_users:
                break

            # If we've already processed this user, skip it
            if handle in self.processed_users:
                continue

            contact_info = profile_scraper.scrape_profile_contact_info(handle)

            if contact_info:
                print("Contact info for", handle, ":", contact_info)
                # Write this single record to CSV immediately
                self.csv_writer.writerow(contact_info)
                self.csv_handle.flush()  # <--- Flush to disk immediately
                self.processed_users.add(handle)
                self.user_count += 1

        # Close tweet detail tab and switch back
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def run(self):
        """Main loop: login, search, scroll, collect tweets, scrape, and stop when max_users is reached."""
        self.login()
        self.search()

        while self.user_count < self.max_users:
            new_tweet_urls = self.collect_tweet_urls()
            print(f"Found {len(new_tweet_urls)} new tweets to process.")

            # If no new tweets found, scroll and try again
            if not new_tweet_urls:
                self.scroll_page(pause=5)
                new_tweet_urls = self.collect_tweet_urls()
                if not new_tweet_urls:
                    print("No new tweets found. Exiting loop.")
                    break

            for tweet_url in new_tweet_urls:
                if self.user_count >= self.max_users:
                    break
                self.process_tweet(tweet_url)

            self.scroll_page(pause=5)

        self.driver.quit()
        self.csv_handle.close()
        print(f"Scraped user info saved to {self.csv_file}")

class ProfileScraper:
    """Scrapes a single Twitter profile for email, phone, Instagram, and WhatsApp links in the bio."""
    def __init__(self, driver):
        self.driver = driver
        self.email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        self.phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
        self.instagram_pattern = re.compile(r'https?://(?:www\.)?instagram\.com/[\w_.]+')
        self.whatsapp_pattern = re.compile(r'https?://(?:wa\.me|api\.whatsapp\.com/send)\S+')

    def scrape_profile_contact_info(self, handle):
        """Open the profile in a new tab, find contact info, close the tab, return a dict."""
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

        # Open the profile in a new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(profile_url)
        time.sleep(5)

        # Scroll to load more content in the bio area
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
        if phones:
            contact_info["phone"] = phones[0]

        instagrams = self.instagram_pattern.findall(page_text)
        if instagrams:
            contact_info["instagram"] = instagrams[0]

        whatsapps = self.whatsapp_pattern.findall(page_text)
        if whatsapps:
            contact_info["whatsapp"] = whatsapps[0]

        # Close this profile tab and go back
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[-1])

        return contact_info
