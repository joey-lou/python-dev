import logging
import os

import requests
from bs4 import BeautifulSoup

from tools.consts import TWILIO_CREDS
from tools.services import SynchronousService
from tools.utils import TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class PlayStationMonitor(SynchronousService):
    """ Scrape static websites for playstation 5 info (availability)
    """

    # gamestop bot-detection can not be by-passed :(
    # GAMESTOP = "https://www.gamestop.com/video-games/playstation-5/consoles/products/playstation-5/11108140.html"
    # target has dynamically loaded component that is not able to be retrieved
    # TARGET = "https://www.target.com/p/playstation-5-console/-/A-81114595"
    BESTBUY = "https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149"
    AMAZON = (
        "https://www.amazon.com/PlayStation-5-Console/dp/B08FC5L3RG?ref_=ast_sto_dp"
    )

    def __init__(self, twilio_sender: TwilioTextSender):
        self.tws = twilio_sender

    def run(self):
        for site, (check_func, web_address) in self._site_map.items():
            status = check_func(self)
            if status:
                msg = f"{site} has available playstation 5 for order!\nGo to: {web_address}"
                logger.info(msg)
                self.tws.send_message(msg)
            else:
                logger.info(f"still no luck at this time from {site}")

    def stop(self):
        quit()

    def _request_headers(self):
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
        }

    def _check_bestbuy(self):
        response = requests.get(self.BESTBUY, headers=self._request_headers())
        soup = BeautifulSoup(response.text, "html.parser")
        buy_button = soup.find_all("button", attrs={"data-sku-id": 6426149})[0]
        if "sold out" == buy_button.text.lower():
            return False
        return True

    def _check_amazon(self):
        response = requests.get(self.AMAZON, headers=self._request_headers())
        soup = BeautifulSoup(response.text, "html.parser")
        availability = soup.find_all("div", id="availability")[0]
        if "unavailable" in availability.text.lower():
            return False
        return True

    _site_map = {
        "amazon": (_check_amazon, AMAZON),
        "bestbuy": (_check_bestbuy, BESTBUY),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    psm = PlayStationMonitor(TwilioTextSender.from_json(TWILIO_CREDS))
    psm.start()
