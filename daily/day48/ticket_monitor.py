import logging
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from tools.consts import CHROME_DRIVER_PATH, TWILIO_CREDS
from tools.services import SynchronousService
from tools.utils import TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class TicketMonitor(SynchronousService):
    """ Scrap websites for ticket info, webdriver version
    """

    SITE = "https://garfieldconservatory.org/visit/"

    DEFAULT_PATH = CHROME_DRIVER_PATH

    def __init__(
        self, twilio_sender: TwilioTextSender, chrome_driver_path: str = DEFAULT_PATH
    ):
        self.tws = twilio_sender
        self.driver = webdriver.Chrome(executable_path=chrome_driver_path)
        self.driver.implicitly_wait(10)  # seconds

    def run(self):
        try:
            status = self._check()
        except NoSuchElementException as e:
            logger.info(f"Layout changed: {e}, assume we managed to find one!")
            status = True
        if status:
            msg = f"{self.SITE} has available ticket!"
            logger.info(msg)
            self.tws.send_message(msg)
            self.stop()
        else:
            logger.info(f"still no luck at this time from {site}")

    def stop(self):
        self.driver.quit()
        quit()

    def _check(self):
        self.driver.get(self.SITE)
        book = self.driver.find_element_by_css_selector(
            "#post-760 > div > div > div > button"
        )
        book.click()
        self.driver.switch_to.frame(0)
        assert (
            len(
                self.driver.find_elements_by_css_selector(
                    "div > table > tbody > tr > td"
                )
            )
            > 5
        ), "Not the right iframe!"

        try:
            self.driver.find_element_by_css_selector(
                "div > table > tbody > tr:nth-child(4) > td:nth-child(7)"
            ).click()
        except:
            return False
        span = self.driver.find_element_by_css_selector(
            "div > table > tbody > tr:nth-child(3) > td:nth-child(7) > span > div > span"
        )
        print(span.text)
        if "not" not in span.text.lower():
            return True
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    psm = TicketMonitor(TwilioTextSender.from_creds_file(TWILIO_CREDS))
    psm.start()
    psm.stop()
