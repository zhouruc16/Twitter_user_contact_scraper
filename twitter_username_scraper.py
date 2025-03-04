import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# --- Regex Patterns for Contact Information ---
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
phone_pattern = re.compile(r'(\+?\d[\d\s\-]{8,}\d)')
instagram_pattern = re.compile(r'https?://(?:www\.)?instagram\.com/[\w_.]+')
whatsapp_pattern = re.compile(r'https?://(?:wa\.me|api\.whatsapp\.com/send)\S+')

# --- Configuration: Set your Chrome user data directory and profile ---
user_data_dir = "/Users/huixian/Library/Application Support/Google"  # Adjust as needed
profile_directory = "Profile 8"  # Your specific profile folder name

chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument(f"--profile-directory={profile_directory}")

# --- Setup ChromeDriver ---
service = Service('./chromedriver-mac-arm64/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

def scrape_profile_contact_info(handle):
    """
    Given a Twitter handle (e.g. '@username'), open the user's profile page
    and search for any email, phone number, Instagram link, or WhatsApp link.
    Returns a dictionary of found contact information.
    """
    contact_info = {
        "handle": handle,
        "email": None,
        "phone": None,
        "instagram": None,
        "whatsapp": None
    }
    # Remove the '@' symbol for constructing the profile URL
    username = handle.lstrip('@')
    profile_url = f"https://twitter.com/{username}"
    print(f"Scraping profile: {profile_url}")
    
    # Open the profile page in a new tab
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(profile_url)
    time.sleep(5)  # Allow the profile page to load

    # Optionally scroll down to load more content
    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    new_height = driver.execute_script("return document.body.scrollHeight")
    
    # Get the page source text to search for contact info
    page_text = driver.page_source

    emails = email_pattern.findall(page_text)
    if emails:
        contact_info["email"] = emails[0]
    
    phones = phone_pattern.findall(page_text)
    if phones:
        contact_info["phone"] = phones[0]
        
    instagrams = instagram_pattern.findall(page_text)
    if instagrams:
        contact_info["instagram"] = instagrams[0]
        
    whatsapps = whatsapp_pattern.findall(page_text)
    if whatsapps:
        contact_info["whatsapp"] = whatsapps[0]
        
    # Close the profile tab and switch back to the tweet detail tab
    driver.close()
    driver.switch_to.window(driver.window_handles[-1])
    
    return contact_info

try:
    # --- Step 1: Log in to Twitter ---
    driver.get("https://twitter.com/login")
    print("Please log in to Twitter manually if necessary. Waiting 5 seconds...")
    time.sleep(5)

    # --- Step 2: Search for a Query ---
    search_query = "dogecoin"  # Change this to your desired search term
    driver.get(f"https://twitter.com/search?q={search_query}&src=typed_query")
    time.sleep(5)

    processed_tweets = set()  # To avoid processing duplicate tweet URLs

    while True:
        # --- Step 3: Collect Tweet URLs from Search Results ---
        tweet_elements = driver.find_elements(By.XPATH, '//article')
        new_tweet_urls = []
        for tweet in tweet_elements:
            try:
                link_element = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                tweet_url = link_element.get_attribute("href")
                if tweet_url not in processed_tweets:
                    new_tweet_urls.append(tweet_url)
            except Exception as e:
                continue

        new_tweet_urls = list(set(new_tweet_urls))
        print(f"Found {len(new_tweet_urls)} new tweets to process.")
        if not new_tweet_urls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            tweet_elements = driver.find_elements(By.XPATH, '//article')
            for tweet in tweet_elements:
                try:
                    link_element = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                    tweet_url = link_element.get_attribute("href")
                    if tweet_url not in processed_tweets:
                        new_tweet_urls.append(tweet_url)
                except Exception as e:
                    continue
            new_tweet_urls = list(set(new_tweet_urls))
            if not new_tweet_urls:
                print("No new tweets found. Exiting loop.")
                break

        # --- Step 4: Process Each Tweet ---
        for tweet_url in new_tweet_urls:
            print(f"\nProcessing tweet: {tweet_url}")
            processed_tweets.add(tweet_url)
            # Open tweet detail page in a new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(tweet_url)
            time.sleep(5)

            # Scroll down to load all comments
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # --- Step 5: Extract the Tweet Poster and Commenter Handles ---
            try:
                original_handle = driver.find_element(
                    By.XPATH, '//article//div[@data-testid="User-Name"]//span[contains(text(),"@")]'
                ).text.strip()
                print("Tweet poster:", original_handle)
            except Exception as e:
                print("Error extracting tweet poster handle:", e)
                original_handle = None

            handles = set()
            articles = driver.find_elements(By.XPATH, '//article')
            for art in articles:
                try:
                    handle = art.find_element(
                        By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(),"@")]'
                    ).text.strip()
                    if handle:
                        handles.add(handle)
                except Exception as e:
                    continue

            print("Handles found in tweet detail page:")
            for h in handles:
                print(h)

            # --- Step 6: For each handle, open their profile and search for contact info ---
            for handle in handles:
                contact_info = scrape_profile_contact_info(handle)
                print("Contact info for", handle, ":", contact_info)

            # Close the tweet detail tab and switch back to the main search results tab
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # --- Step 7: Scroll down in the main tab to load more tweets ---
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

finally:
    driver.quit()
