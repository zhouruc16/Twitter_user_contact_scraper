import os
from twitter_username_scraper import TwitterScraper

if __name__ == "__main__":
    try:
        DRIVER_PATH = './chromedriver_win64/chromedriver.exe'
        USER_DATA_DIR = None
        PROFILE_DIRECTORY = None

        # Ask user for a search query
        SEARCH_QUERY = input("Enter a hashtag or keyword to scrape (e.g. '#dogecoin' or 'dogecoin'): ")  # <-- Added

        # Ask how many users we want to scrape
        max_users = int(input("Enter how many users you want to fetch: "))  # <-- Added

        # Always write to a single CSV file (no timestamp)
        CSV_FILE = "scraped_user_info.csv"  # <-- Updated

        # Initialize and run the scraper
        scraper = TwitterScraper(
            driver_path=DRIVER_PATH,
            csv_file=CSV_FILE,
            search_query=SEARCH_QUERY,
            headless=False,
            user_data_dir=USER_DATA_DIR,
            profile_directory=PROFILE_DIRECTORY,
            max_users=max_users        # <-- Added
        )
        scraper.run()
    except Exception as e:
        print(e)
