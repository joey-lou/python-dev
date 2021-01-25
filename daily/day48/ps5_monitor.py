import logging
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from tools.consts import CHROME_DRIVER_PATH, TWILIO_CREDS
from tools.services import SynchronousService
from tools.utils import TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class PlayStationMonitor(SynchronousService):
    """ Scrap websites for playstation info, webdriver version
    """

    GAMESTOP = "https://www.gamestop.com/video-games/playstation-5/consoles/products/playstation-5/11108140.html"
    TARGET = "https://www.target.com/p/playstation-5-console/-/A-81114595"
    BESTBUY = "https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149"
    AMAZON = (
        "https://www.amazon.com/PlayStation-5-Console/dp/B08FC5L3RG?ref_=ast_sto_dp"
    )

    DEFAULT_PATH = CHROME_DRIVER_PATH

    def __init__(
        self, twilio_sender: TwilioTextSender, chrome_driver_path: str = DEFAULT_PATH
    ):
        self.tws = twilio_sender
        self.driver = webdriver.Chrome(executable_path=chrome_driver_path)
        self.driver.implicitly_wait(10)  # seconds

    def run(self):
        for site, (check_func, web_address) in self._site_map.items():
            try:
                status = check_func(self)
            except NoSuchElementException as e:
                logger.info(f"Layout changed: {e}, assume we managed to find one!")
                status = True
            if status:
                msg = f"{site} has available playstation 5 for order!\nGo to: {web_address}"
                logger.info(msg)
                self.tws.send_message(msg)
                self.stop()
            else:
                logger.info(f"still no luck at this time from {site}")

    def stop(self):
        self.driver.quit()
        quit()

    def _check_gamestop(self):
        self.driver.get(self.GAMESTOP)
        not_available_text = self.driver.find_element_by_css_selector(
            "button.add-to-cart"
        ).text
        logger.info(f"_check_gamestop: {not_available_text}")
        if "not available" in not_available_text.lower():
            return False
        return True

    def _check_bestbuy(self):
        self.driver.get(self.BESTBUY)
        sold_out = self.driver.find_element_by_css_selector(
            "button.add-to-cart-button"
        ).text
        logger.info(f"_check_bestbuy: {sold_out}")
        if "sold out" in sold_out.lower():
            return False
        return True

    def _check_target(self):
        self.driver.get(self.TARGET)
        sold_out = self.driver.find_element_by_css_selector(
            "div.h-text-orangeDark"
        ).text
        logger.info(f"_check_target: {sold_out}")
        if "sold out" in sold_out.lower():
            return False
        return True

    def _check_amazon(self):
        self.driver.get(self.AMAZON)
        unavailable = self.driver.find_element_by_id("availability").text
        logger.info(f"_check_amazon: {unavailable}")
        if "unavailable" in unavailable.lower():
            return False
        return True

    _site_map = {
        "amazon": (_check_amazon, AMAZON),
        "target": (_check_target, TARGET),
        "bestbuy": (_check_bestbuy, BESTBUY),
        "gamestop": (_check_gamestop, GAMESTOP),
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    psm = PlayStationMonitor(TwilioTextSender.from_json(TWILIO_CREDS))
    psm.run()
    psm.stop()
