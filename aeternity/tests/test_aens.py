import random
import string

from nose.tools import *

from aeternity import Config
from aeternity.aens import InvalidName, Name

Config.set_default(Config(local_port=3013, internal_port=3113, websocket_port=3114))

def random_domain(length=10):
    rand_str = ''.join(random.choice(string.ascii_letters) for _ in range(length))
    return rand_str + '.aet'

@raises(InvalidName)
def test_name_validation_fails():
    name = Name('test.lol')

def test_name_validation_succeeds():
    name = Name('test.aet')

def test_name_is_available():
    name = Name(random_domain())
    assert name.is_available()

