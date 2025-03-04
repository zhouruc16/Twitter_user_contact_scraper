import datetime
from twitter_scraper import TwitterScraper

if __name__ == "__main__":
    DRIVER_PATH = './chromedriver-mac-arm64/chromedriver'
    # Set these to None if you don't want to use a specific user data directory or profile
    USER_DATA_DIR = None  
    PROFILE_DIRECTORY = None  
    # Create a timestamped CSV file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CSV_FILE = f"scraped_user_info_{timestamp}.csv"
    # Supply either a hashtag (e.g., "#dogecoin") or a keyword (e.g., "dogecoin")
    SEARCH_QUERY = "#dogecoin"  # or "dogecoin"

    scraper = TwitterScraper(
        DRIVER_PATH,
        CSV_FILE,
        SEARCH_QUERY,
        headless=False,
        user_data_dir=USER_DATA_DIR,
        profile_directory=PROFILE_DIRECTORY
    )
    scraper.run()
