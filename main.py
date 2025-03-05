import os
import datetime
from twitter_username_scraper import TwitterScraper

if __name__ == "__main__":
    DRIVER_PATH = './chromedriver-mac-arm64/chromedriver'
    # Optional user data and profile directories. Set to None if not used.
    USER_DATA_DIR = None
    PROFILE_DIRECTORY = None
    
    # Supply either a hashtag (e.g., "#dogecoin") or a keyword (e.g., "dogecoin")
    SEARCH_QUERY = "#保健品"  # or "dogecoin"
    
    # Prepare directory structure: base directory "scraped_user_info", then subdirectory by the query string (without the '#' symbol)
    base_dir = "scraped_user_info"
    query_dir = SEARCH_QUERY.strip()
    query_dir_path = os.path.join(base_dir, query_dir)
    os.makedirs(query_dir_path, exist_ok=True)
    
    # Create a timestamped CSV file name inside the query subdirectory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CSV_FILE = os.path.join(query_dir_path, f"scraped_user_info_{timestamp}.csv")
    
    scraper = TwitterScraper(
        DRIVER_PATH,
        CSV_FILE,
        SEARCH_QUERY,
        headless=False,
        user_data_dir=USER_DATA_DIR,
        profile_directory=PROFILE_DIRECTORY
    )
    scraper.run()
