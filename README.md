# aeternity-dev-tools

## Introduction

This repo is for tools and notes for working with aeternity when you're running
an epoch node on your local machine.

## Usage

### Oracles

Oracles are a means to provide external data in the block chain which then
can be used in smart contracts. There are two roles when using an oracle:

    - Oracle Operator ("hosts" the oracle and responds to queries)
    - Oracle User (sends queries to the oracle)

To provide an Oracle on the block chain, you have to inherit from aeternity.Oracle
and implement `get_reply` which will be passed a `message` when a request to
this oracle was found in the block chain.

Furthermore you must specify `query_format`, `response_format`,
`default_query_fee`, `default_fee`, `default_query_ttl`, `default_response_ttl`

For example:
```
from aeternity import Oracle

class WeatherOracle(Oracle):
    query_format = 'weather_query2'
    response_format = 'weather_resp2'
    default_query_fee = 4
    default_fee = 6
    default_query_ttl = 10
    default_response_ttl = 10

    def get_reply(self, message):
        return '26 C'
```

To act as operator of this oracle, you have to connect to your local epoch node
(see [https://github.com/aeternity/epoch](https://github.com/aeternity/epoch] to
find out how to run a local node), instantiate your oracle and
register it on the block chain.

```
from aeternity import Config, EpochClient
# example configuration to create a connection to your node:
config = Config(local_port=3013, internal_port=3113, websocket_port=3114)
# connect with the epoch node
client = EpochClient(config=config)
# instantiate and register your oracle
client.register_oracle(WeatherOracle())
# listen to all events on the block chain and respond to all queries
client.run()
```

### AENS (aeternity name system)

To register human-readable names with the aeternity naming system you also need
to connect to your local epoch node.

```
from aeternity import Config, EpochClient, Name
import sys
# create connection with the local node:
config = Config(local_port=3013, internal_port=3113, websocket_port=3114)
client = EpochClient(config)

# try registering 'example.aet' on the block chain:
name = Name(domain='example.aet')
# before trying to register, make sure that the name is still available
if not name.check_available():
    print('Name is not available anymore!')
    sys.exit(1)
#
name.preclaim()
# alternatively you can also call `claim`, which isn't blocking, but raises a
# `ClaimException` if there is an error claiming the domain.
name.claim_blocking()
name.update(target='ak$1234deadbeef')
# you can also pass an oracle instance directly to in the target parameter,
# e.g.
# oracle = WeatherOracle()
# client.register_oracle(oracle)
# name.update(target=oracle)

```

