import random
import string

from nose.tools import *

from aeternity import Config, EpochClient
from aeternity.aens import InvalidName, Name
from aeternity.config import ConfigException

# to run this test in other environments set the env vars as specified in the
# config.py
try:
    # if there are no env vars set for the config, this call will fail
    Config()
except ConfigException:
    # in this case we create a default config that should work on the dev
    # machines.
    Config.set_default(Config(local_port=3013, internal_port=3113, websocket_port=3114))


def random_domain(length=10):
    rand_str = ''.join(random.choice(string.ascii_letters) for _ in range(length))
    return rand_str + '.aet'

@raises(InvalidName)
def test_name_validation_fails():
    Name('test.lol')

def test_name_validation_succeeds():
    Name('test.aet')

def test_name_is_available():
    name = Name(random_domain())
    assert name.is_available()

def test_name_status_availavle():
    name = Name(random_domain())
    assert name.status == Name.Status.UNKNOWN
    name.update_status()
    assert name.status == Name.Status.AVAILABLE

def test_name_claim_lifecycle():
    domain = random_domain()
    name = Name(domain)
    assert name.status == Name.Status.UNKNOWN
    name.update_status()
    assert name.status == Name.Status.AVAILABLE
    name.preclaim()
    assert name.status == Name.Status.PRECLAIMED
    name.claim_blocking()
    assert name.status == Name.Status.CLAIMED

def test_name_status_unavailable():
    # claim a domain
    domain = random_domain()
    occupy_name = Name(domain)
    occupy_name.preclaim()
    occupy_name.claim_blocking()
    # wait for the state to propagate in the block chain
    EpochClient().wait_for_next_block()
    same_name = Name(domain)
    assert not same_name.is_available()

def test_name_update():
    client = EpochClient()
    # claim a domain
    domain = random_domain()
    name = Name(domain)
    name.preclaim()
    name.claim_blocking()
    name.update(target=client.get_pubkey())
