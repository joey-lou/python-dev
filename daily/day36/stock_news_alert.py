import datetime as dt
import logging
import os
from typing import Dict, List, NamedTuple

import requests

from tools.consts import FINNHUB_CREDS, TWILIO_CREDS
from tools.services import SynchronousService
from tools.utils import BaseCreds, TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class FinnhubCreds(BaseCreds):
    api_key: str


CONFIG = {
    "finnhub_creds_loc": FINNHUB_CREDS,
    "ticker": "TSLA",
    "twilio_creds_loc": TWILIO_CREDS,
    "threshold": 0.03,
}


class QuoteData(NamedTuple):
    dt: dt.datetime
    previous_close: float
    current: float
    move: float


class NewsData(NamedTuple):
    id: int
    dt: dt.datetime
    headline: str
    summary: str
    url: str


class StockPriceMonitor(SynchronousService):
    """ Monitor stock movements during day since last closing price
        If price dips or rises beyond threshold, alert user with most recent news

        Potentially improements such as tracking history of movement and sending smarter alerts:
        1. if previously alerted and the price moved in opposite direction (reaching below threshold)
            we may send an alert saying now the price movement has reverted
        2. if price moved in same direction but only by a bit, we can say the price move persisted,
            and send updated news
    """

    DEFAULT_THRESHOLD = 0.03

    def __init__(
        self,
        ticker: str,
        finnhub_creds: FinnhubCreds,
        text_sender: TwilioTextSender,
        news_alert: bool = True,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.text_sender = text_sender
        self._ticker = ticker
        self._creds = finnhub_creds
        self._quote = None
        self._threshold = threshold
        self._news_alert = news_alert
        self._news_cache = {}  # track news we have seen already

    @classmethod
    def from_serializable(cls, config: Dict):
        ticker = config["ticker"]
        finnhub_creds = FinnhubCreds.from_json_file(config["finnhub_creds_loc"])
        text_sender = TwilioTextSender.from_creds_file(config["twilio_creds_loc"])
        news_alert = config.get("news_alert") or True
        threshold = config.get("threshold") or cls.DEFAULT_THRESHOLD
        return cls(ticker, finnhub_creds, text_sender, news_alert, threshold)

    def run(self):
        """
        1. get most recent quote
        2. check for price movement
        3. check if movement beyond threshold, get news (if specified)
        4. if 3 is true, send message
        """
        logger.info(f"checking price for {self._ticker}")
        self._quote = self.load_quote(self._ticker, self._creds.api_key)
        if self.is_alert_move(self._quote, self._threshold):
            self.send_alert()
        else:
            logger.info(f"no alert-worthy movements observed for {self._ticker}")

    def stop(self):
        # no state to cleanup, simply exit program
        quit()

    @staticmethod
    def load_quote(ticker, api_key) -> QuoteData:
        """ check finnhub API: https://finnhub.io/docs/api#quote
        """
        r = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={api_key}"
        )
        r.raise_for_status()
        quote_data = r.json()
        quote_data["dt"] = dt.datetime.utcfromtimestamp(
            quote_data["t"]
        )  # convert unix time to datetime object
        quote_data["previous_close"] = quote_data["pc"]
        quote_data["current"] = quote_data["c"]
        quote_data["move"] = quote_data["c"] / quote_data["pc"] - 1
        quote = QuoteData(
            **{k: v for k, v in quote_data.items() if k in QuoteData._fields}
        )
        logger.info(f"loaded quote: {quote}")
        return quote

    @staticmethod
    def is_alert_move(quote: QuoteData, threshold: float) -> bool:
        move_frac = abs(quote.current - quote.previous_close) / quote.previous_close
        return move_frac >= threshold

    @staticmethod
    def _make_quote_message(quote: QuoteData, ticker: str):
        return f"{ticker} {'🔻' if quote.move < 0 else '🔺'} {quote.move:.1%}, ${quote.previous_close}->${quote.current}\n"

    @staticmethod
    def load_news(ticker, api_key) -> List[NewsData]:
        """ retrieves all the news on the day
        """
        day = dt.date.today().strftime("%Y-%m-%d")
        r = requests.get(
            f"https://finnhub.io/api/v1/company-news?symbol={ticker}&token={api_key}&from={day}&to={day}"
        )
        r.raise_for_status()
        news_data = r.json()
        news = []
        for data in news_data:
            data["dt"] = dt.datetime.utcfromtimestamp(data["datetime"])
            news.append(
                NewsData(**{k: v for k, v in data.items() if k in NewsData._fields})
            )
        logger.info(f"loaded {len(news)} news")
        return news

    @staticmethod
    def _format_news(news: List[NewsData]):
        if not news:
            return "No news is new."
        msg = "Headlines:\n"
        for n in sorted(news, key=lambda x: x.dt):
            msg += f"{n.dt}: {n.headline}\n"
        return msg

    def _get_fresh_news(self, news: List[NewsData]):
        """ cache news and return news message
        """
        fresh_news = []
        for n in news:
            if n.id in self._news_cache:
                continue
            self._news_cache[n.id] = n
            fresh_news.append(n)
        return self._format_news(fresh_news)

    def send_alert(self):
        msg = self._make_quote_message(self._quote, self._ticker)
        if self._news_alert:
            news = self.load_news(self._ticker, self._creds.api_key)
            msg += self._get_fresh_news(news)
        self.text_sender.send_message(msg)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    spm = StockPriceMonitor.from_serializable(CONFIG)
    spm.start()
