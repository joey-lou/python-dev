from tools.consts import FINNHUB_CREDS
from typing import List

class StockPriceMonitor:
    """ Monitor stock movements during day since last closing price
        If price dips or rises beyond threshold, alert user with most recent news
    """
    DEFAULT_INTERVAL = 60

    def __init__(self, ticker: str, api_key: str, news_alert: bool = True):
        self.ticker = ticker
        self._api_key = api_key

    @classmethod
    def from_json(cls):
        return cls()


    def start():
        """ simply invoke run and go to sleep until time is up
        """
        raise NotImplementedError

    def run():
        """
        1. check current time
          1.1. see if task need to be run (might be outside trading window?)
          1.2. see if past closing price need to be loaded
        2. get most recent price
        3. check for price movement
        4. check if movement beyond threshold, get news (if specified)
        5. if 4 is true, send message
        """
        raise NotImplementedError
    
    def load_last_day_close():
        raise NotImplementedError

    def get_current_price():
        """ query for last close price (last minute)
            and compare against previous close
        """
        raise NotImplementedError
    
    def get_news_for_ticker():
        raise NotImplementedError

    def send_alert():
        raise NotImplementedError



if __name__ == "__main__":
    print(1)
