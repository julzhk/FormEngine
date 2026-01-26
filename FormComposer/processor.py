from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class Processor(ABC):
    @abstractmethod
    def process(self, data):
        pass

class PetProcessor(Processor):
    def process(self, data):
        print(f"PetProcessor logging data: {data}")
        logger.info(f"PetProcessor processing data: {data}")
