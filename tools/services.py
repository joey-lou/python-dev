import logging
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SynchronousService(ABC):
    """ Very simple synchronous service template
    """

    DEFAULT_INTERVAL = 3600  # default to hourly update

    def start(self, interval: int = DEFAULT_INTERVAL):
        """ simply invoke run and go to sleep until time is up
        """
        logger.info(f"starting {self.__class__.__name__}")
        while True:
            self.run()
            logger.info(f"sleeping for {interval}")
            time.sleep(interval)

    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError
