import json
import random

from aeternity.oracle import EpochClient, Oracle


class ClaimException(Exception):
    pass


class MissingPreclaim(ClaimException):
    pass


class TooEarlyClaim(ClaimException):
    pass


class InvalidName(Exception):
    pass


class NameStatus:
    UNKNOWN = 'UNKNOWN'
    AVAILABLE = 'AVAILABLE'
    CLAIMED = 'CLAIMED'


class Name:
    def __init__(self, domain, client=None):
        if client is None:
            client = EpochClient()
        self.__class__.validate_name(domain)

        self.client = client
        self.domain = domain
        self.status = NameStatus.UNKNOWN
        self.preclaimed_block_height = None
        # this is set after being claimed
        self.name_hash = None
        self.name_ttl = 0
        self.pointers = []

    @classmethod
    def validate_name(cls, domain):
        # TODO: validate according to the spec!
        # TODO: https://github.com/aeternity/protocol/blob/master/AENS.md#name
        if not domain.endswith(('.aet', '.test')):
            raise InvalidName('AENS TLDs must end in .aet')

    def update_status(self):
        response = self.client.local_http_get('name', params={'name': self.domain})
        if response.get('reason') == 'Name not found':
            self.status = NameStatus.AVAILABLE
        else:
            self.status = NameStatus.CLAIMED
            self.name_hash = response['name_hash']
            self.name_ttl = response['name_ttl']
            self.pointers = response['pointers']

    def check_available(self):
        self.update_status()
        return self.status == NameStatus.AVAILABLE

    def check_claimed(self):
        self.update_status()
        return self.status == NameStatus.CLAIMED

    def preclaim(self):
        # check which block we used to create the preclaim
        self.preclaimed_block_height = self.client.get_top_block()
        salt = random.randint(0, 2**64)
        response = self.client.local_http_get(
            'commitment-hash',
            params={'name': self.domain, 'salt': salt}
        )
        commitment_hash = response['commitment']
        response = self.client.local_http_post(
            'name-preclaim-tx',
            json={"commitment": commitment_hash, "fee": 1}
        )
        print('preclaim response')
        print(response)

    def claim_blocking(self):
        self.client.wait_for_next_block()
        self.claim()

    def claim(self):
        if self.preclaimed_block_height is None:
            raise MissingPreclaim('You must call preclaim before claiming a name')
        current_block_height = self.client.get_top_block()
        if self.preclaimed_block_height >= current_block_height:
            raise TooEarlyClaim(
                'You must wait for one block to call claim.'
                'Use `claim_blocking` if you have a lot of time on your hands'
            )

    def update(self, target):
        assert self.status == NameStatus.CLAIMED, 'Must be claimed to update pointer'

        if isinstance(target, Oracle):
            if target.oracle_id is None:
                raise ValueError('You must register the oracle before using it as target')
            target = target.oracle_id

        if target.startswith('ak'):
            pointers = {'account_pubkey': target}
        else:
            pointers = {'oracle_pubkey': target}

        response = self.client.local_http_post(
            'name-update-tx',
            json={
                "name_hash": self.name_hash,
                "name_ttl": self.name_ttl,
                "ttl": 50,
                "pointers": json.dumps(pointers),
                "fee": 1
            }
        )
        print(response)
