import dataclasses
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Processor(ABC):
    def process(self, data, form):
        # data is expected to be avro serialized bytes
        print(f" processing data: {data}")
        deserialized_dict = form.avro_deserialize(data)
        print(f" logging data: {deserialized_dict}")
        logger.info(f" processing data: {deserialized_dict}")
        self.do_process(deserialized_dict)

    @abstractmethod
    def do_process(self, data_dict:dict):
        pass

class PetProcessor(Processor):
    @dataclasses.dataclass
    class Data:
        q1: str|None = None

    def do_process(self,data_dict:dict):
        data:'Data' = self.__class__.Data(**data_dict)
        print(f"PetProcessor processing data: {data}")

