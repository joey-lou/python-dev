import os

file_dir = os.path.dirname(__file__)
ROOT_DIR = os.path.join(file_dir, "..", "secret")
OPENWEATHER_CREDS = os.path.join(ROOT_DIR, "openweather_creds.json")
TWILIO_CREDS = os.path.join(ROOT_DIR, "twilio_creds.json")
FINNHUB_CREDS = os.path.join(ROOT_DIR, "finnhub_creds.json")
PIXELA_CREDS = os.path.join(ROOT_DIR, "pixela_creds.json")
SHEETY_CREDS = os.path.join(ROOT_DIR, "sheety_creds.json")
KIWI_CREDS = os.path.join(ROOT_DIR, "kiwi_creds.json")
SPOTIFY_CREDS = os.path.join(ROOT_DIR, "spotify_creds.json")
# chrom dirver needs to be installed manually
CHROME_DRIVER_PATH = "/Users/joeylou/Development/chromedriver"
