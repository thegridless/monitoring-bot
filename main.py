import requests
from bs4 import BeautifulSoup
import time
import hashlib
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NewsMonitor:
    def __init__(self):
        self.url = "https://it.tlscontact.com/by/msq/page.php?pid=news"
        self.previous_content_hash = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Get Telegram credentials from environment variables
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        # Get chat IDs and split them into a list
        chat_ids = os.getenv('TELEGRAM_CHAT_IDS', '')
        self.telegram_chat_ids = [chat_id.strip() for chat_id in chat_ids.split(',') if chat_id.strip()]
        
        if not self.telegram_bot_token:
            raise ValueError("Telegram bot token not found in environment variables")
        if not self.telegram_chat_ids:
            raise ValueError("No Telegram chat IDs found in environment variables")

    def get_page_content(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.send_telegram_message(f"Error fetching the page: {e}")
            return None

    def extract_news_content(self, html_content):
        if not html_content:
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the news content section - you might need to adjust this selector
        news_section = soup.find('div', class_='news-content')
        return news_section.text.strip() if news_section else None

    def get_content_hash(self, content):
        if not content:
            return None
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def send_telegram_message(self, message):
        for chat_id in self.telegram_chat_ids:
            try:
                telegram_api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML"  # Enable HTML formatting
                }
                response = requests.post(telegram_api_url, json=payload)
                response.raise_for_status()
                print(f"Message sent successfully to chat ID: {chat_id}")
            except Exception as e:
                print(f"Failed to send Telegram message to chat ID {chat_id}: {e}")

    def log_change(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.send_telegram_message(formatted_message)

    def check_for_updates(self):
        content = self.get_page_content()
        news_content = self.extract_news_content(content)
        
        if not news_content:
            self.log_change("Failed to fetch or parse content")
            return

        current_hash = self.get_content_hash(news_content)

        if not self.previous_content_hash:
            self.log_change("Initial content loaded")
            self.previous_content_hash = current_hash
        elif current_hash != self.previous_content_hash:
            self.log_change(f"New content detected!\n\nContent:\n{news_content}")
            self.previous_content_hash = current_hash

    def run(self, check_interval=300):  # 300 seconds = 5 minutes
        startup_message = f"Starting monitoring of {self.url}\nChecking every {check_interval} seconds"
        print(startup_message)
        self.send_telegram_message(startup_message)
        
        while True:
            self.check_for_updates()
            time.sleep(check_interval)

if __name__ == "__main__":
    monitor = NewsMonitor()
    monitor.run()
