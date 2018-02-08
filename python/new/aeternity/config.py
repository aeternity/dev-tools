import os

import requests


class Config:
    default_config = None

    def __init__(self, local_port=None, internal_port=None, websocket_port=None, host='localhost'):
        if local_port is None:
            local_port = os.environ['AE_LOCAL_PORT']
        self.local_port = local_port
        if internal_port is None:
            internal_port = os.environ['AE_LOCAL_INTERNAL_PORT']
        self.local_internal_port = internal_port
        if websocket_port is None:
            websocket_port = os.environ['AE_WEBSOCKET']
        self.websocket_port = websocket_port
        self.websocker_url = f'ws://{host}:{self.websocket_port}/websocket'
        self.http_api_url = f'http://{host}:{self.local_port}/v2'
        self.internal_api_url = f'http://{host}:{self.local_internal_port}/v2'

        self.pub_key = None

    @property
    def top_block_url(self):
        return f'{self.http_api_url}/top'

    @property
    def pub_key_url(self):
        return f'{self.internal_api_url}/account/pub-key'

    def get_pub_key(self):
        if self.pub_key is None:
            self.pub_key = requests.get(self.pub_key_url).json()['pub_key']
        return self.pub_key

    @classmethod
    def set_default(cls):
        """
        sets the default configuration that will be used when the epoch client
        did not get a config passed into its constructor

        :return: None
        """
        cls.default_config = Config()

    @classmethod
    def get_default(cls):
        """
        returns the previously set default config or constructs a configuration
        automatically from environment variables

        :return: Config
        """
        if cls.default_config is None:
            cls.default_config = Config()
        return cls.default_config
