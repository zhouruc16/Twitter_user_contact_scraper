from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# ====== Configuration ======
# Path to your Chrome user data directory (adjust for your OS)
user_data_dir = "/Users/huixian/Library/Application Support/Google"  # For Windows example: "C:/Users/YourUser/AppData/Local/Google/Chrome/User Data"
profile_directory = "Profile 8"  # or your specific profile folder name

chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
chrome_options.add_argument(f"--profile-directory={profile_directory}")

# ====== Setup ChromeDriver ======
service = Service('./chromedriver-mac-arm64/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # ====== Step 1: Log In to Twitter ======
    driver.get("https://twitter.com/login")
    print("Please log in to Twitter manually if necessary. Waiting 5 seconds...")
    time.sleep(5)  # Adjust wait time as needed

    # ====== Step 2: Search for a Query ======
    search_query = "dogecoin"  # Change this to your desired search term
    driver.get(f"https://twitter.com/search?q={search_query}&src=typed_query")
    time.sleep(5)  # Wait for the search results page to load

    # Set to store tweet URLs that have been processed
    processed_tweets = set()

    # Main loop: scroll and process new tweets
    while True:
        # ====== Step 3: Collect Tweet URLs from Search Results ======
        tweet_elements = driver.find_elements(By.XPATH, '//article')
        new_tweet_urls = []
        for tweet in tweet_elements:
            try:
                # Locate a link to the tweet detail page (should contain "/status/")
                link_element = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]")
                tweet_url = link_element.get_attribute("href")
                if tweet_url not in processed_tweets:
                    new_tweet_urls.append(tweet_url)
            except Exception as e:
                continue

        # Remove duplicate URLs
        new_tweet_urls = list(set(new_tweet_urls))
        print(f"Found {len(new_tweet_urls)} new tweets to process.")

        # If no new tweets were found after scrolling, exit the loop
        if not new_tweet_urls:
            # Scroll down to load more tweets
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            # Check again for new tweets
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

        # ====== Step 4: Process Each New Tweet ======
        for tweet_url in new_tweet_urls:
            print(f"\nProcessing tweet: {tweet_url}")
            processed_tweets.add(tweet_url)

            # Open the tweet detail page in a new tab
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(tweet_url)
            time.sleep(5)  # Wait for the tweet detail page to load

            # Scroll down in the tweet detail page to load all comments
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Wait for new content to load
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # ====== Step 5: Extract the Tweet Poster and Commenter Handles ======
            try:
                # Extract the tweet poster's handle from the main tweet article
                original_handle = driver.find_element(
                    By.XPATH, '//article//div[@data-testid="User-Name"]//span[contains(text(),"@")]'
                ).text.strip()
                print("Tweet poster:", original_handle)
            except Exception as e:
                print("Error extracting tweet poster handle:", e)
                original_handle = None

            # Collect handles from all articles (tweets/comments) on the detail page
            handles = set()
            articles = driver.find_elements(By.XPATH, '//article')
            for art in articles:
                try:
                    handle = art.find_element(
                        By.XPATH, './/div[@data-testid="User-Name"]//span[contains(text(),"@")]'
                    ).text.strip()
                    # You can choose to exclude the original poster by uncommenting:
                    # if handle == original_handle:
                    #     continue
                    if handle:
                        handles.add(handle)
                except Exception as e:
                    continue

            print("Handles found in this tweet detail page:")
            for h in handles:
                print(h)

            # Close the tweet detail tab and switch back to the main search results tab
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # ====== Step 6: Scroll Down in the Main Tab to Load More Tweets ======
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Allow time for additional tweets to load

finally:
    # ====== Cleanup: Close the Browser ======
    driver.quit()
