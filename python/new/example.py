#!/usr/env/bin python
import logging

from aeternity.config import Config
from aeternity.oracle import EpochClient
from aeternity.oracle import Oracle


logging.basicConfig(level=logging.DEBUG)


class WeatherOracle(Oracle):
    query_format = 'weather_query'
    response_format = 'weather_resp'
    default_query_fee = 0
    default_fee = 6
    default_ttl = 2000

    def get_reply(self, request):
        return '26 C'


config = Config(local_port=3013, internal_port=3113, websocket_port=3114)
weather_oracle = WeatherOracle()
client = EpochClient(config=config)
client.mount(weather_oracle)
client.run()
