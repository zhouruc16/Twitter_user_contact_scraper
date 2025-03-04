# Twitter Profile Scraper

This project is an object-oriented Twitter scraper built using Selenium. It searches Twitter for tweets matching a given hashtag or keyword, then extracts contact information from the profiles of tweet posters and commenters. The scraped data is saved to a timestamped CSV file.

## Features

- **Search Flexibility:**  
  Search Twitter by providing either a hashtag (e.g., `#dogecoin`) or a keyword (e.g., `dogecoin`).

- **Tweet & Profile Scraping:**  
  - Collect tweet URLs from Twitter search results.
  - Open each tweet in a new browser tab and scroll down to load all comments.
  - Extract the tweet poster’s handle and commenter handles.
  - Visit each user’s profile and scrape contact details (email, phone number, Instagram, and WhatsApp links) from the profile box.

- **Anti-Bot Measures:**  
  The code includes several Chrome options (e.g., a randomized user agent, disabling certain automation features) to help prevent detection as a bot.

- **CSV Output:**  
  Each run of the script produces a CSV file with a timestamped filename, and data is written incrementally as it is scraped.

- **Optional Chrome Profile Usage:**  
  You can optionally supply a custom Chrome user data directory and profile. If not provided, the scraper will run with default settings.

## Prerequisites

- **Python:** Python 3.8 or higher is recommended.
- **Selenium:** Version 4.29.0  
- **webdriver-manager:** Version 4.0.2 (Optional—if you prefer to automatically manage ChromeDriver; the current implementation uses a specified driver path)
- **Other Python Standard Libraries:** `re`, `csv`, `time`, `datetime`, `random`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/twitter-profile-scraper.git
   cd twitter-profile-scraper
   ```
   
2. **Install Dependencies:**

    Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

    Install required packages using pip:

    ```bash
    pip install -r requirements.txt
    ```
    


## Project Structure
- `twitter_scraper.py`
    Contains the main classes:

    - `TwitterScraper`: Handles logging in, searching for tweets, collecting tweet URLs, processing tweets, and writing scraped data to CSV.
    - `ProfileScraper`: Opens individual Twitter profiles and scrapes the contact information from the profile box.
  
- main.py
The entry point for the application. It imports `TwitterScraper`, sets parameters (including optional Chrome user data directory and profile), and runs the scraper.

## Usage
1. Configure Settings:
    Edit `main.py` to set your parameters. For example:

   - **DRIVER_PATH**: Path to your ChromeDriver executable.
   - **USER_DATA_DIR & PROFILE_DIRECTORY**: Set to your Chrome user data directory and profile (optional). Use None if not needed.
   - **SEARCH_QUERY**: Provide a hashtag (e.g., #dogecoin) or a keyword (e.g., dogecoin).
   - **CSV_FILE**: The output file is automatically timestamped.

2. Run the Scraper:

    ```bash
    python main.py
    ```

    The script will open Twitter's login page. Log in manually (you have a set wait time, e.g., 30 seconds) before the scraper starts searching for tweets and collecting data.


3. View Results:
    The scraped data is written to a CSV file named similar to `scraped_user_info_YYYYMMDD_HHMMSS.csv` in the project directory.

## Disclaimer
- Terms of Service:
Scraping Twitter may violate their terms of service. Ensure you have the right to scrape and use this data. Use this tool responsibly and at your own risk.

- Legal Considerations:
The author is not responsible for any misuse or legal issues arising from using this code. Always comply with local laws and website policies.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

##Contact
For questions or contributions, please open an issue or contact thomas@borderxai.com.