import json
import random

from aeternity.oracle import EpochClient, Oracle

class InvalidName(Exception):
    pass


class GeneralClaimException(Exception):
    pass


class MissingPreclaim(GeneralClaimException):
    pass


class PreclaimFailed(GeneralClaimException):
    pass


class TooEarlyClaim(GeneralClaimException):
    pass


class ClaimFailed(GeneralClaimException):
    pass


class NameStatus:
    UNKNOWN = 'UNKNOWN'
    AVAILABLE = 'AVAILABLE'
    PRECLAIMED = 'PRECLAIMED'
    CLAIMED = 'CLAIMED'


class Name:
    Status = NameStatus

    def __init__(self, domain, client=None):
        if client is None:
            client = EpochClient()
        self.__class__.validate_name(domain)

        self.client = client
        self.domain = domain
        self.status = NameStatus.UNKNOWN
        # set after preclaimed:
        self.preclaimed_block_height = None
        self.preclaimed_commitment_hash = None
        self.preclaim_salt = None
        # set after claimed
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

    def is_available(self):
        self.update_status()
        return self.status == NameStatus.AVAILABLE

    def check_claimed(self):
        self.update_status()
        return self.status == NameStatus.CLAIMED

    def preclaim(self):
        # check which block we used to create the preclaim
        self.preclaimed_block_height = self.client.get_top_block()
        self.preclaim_salt = random.randint(0, 2**64)
        response = self.client.local_http_get(
            'commitment-hash',
            params={
                'name': self.domain,
                'salt': self.preclaim_salt
            }
        )
        try:
            commitment_hash = response['commitment']
        except KeyError:
            raise PreclaimFailed(response)
        response = self.client.internal_http_post(
            'name-preclaim-tx',
            json={
                "commitment": commitment_hash,
                "fee": 1
            },
        )
        try:
            # the response is an empty dict if the call failed error
            self.preclaimed_commitment_hash = response['commitment']
            self.status = NameStatus.PRECLAIMED
        except KeyError:
            raise PreclaimFailed(response)

    def claim_blocking(self):
        try:
            self.claim()
        except TooEarlyClaim:
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

        response = self.client.internal_http_post(
            'name-claim-tx',
            json={
                'name': self.domain,
                'name_salt': self.preclaim_salt,
                'fee': 1
            }
        )
        try:
            self.name_hash = response['name_hash']
            self.status = Name.Status.CLAIMED
        except KeyError:
            raise ClaimFailed(response)

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

    def transfer_ownership(self, receipient_pubkey):
        # TODO
        pass

    def revoke(self):
        # TODO
        pass
