# Python client for NervesHub

A thin wrapper around the NervesHub User API

See https://github.com/nerves-hub/nerves_hub_user_api for more details.

## Usage

Set up your environment

```bash
export NERVES_HUB_ORG="MY ORG"
export NERVES_HUB_PRODUCT="MY PRODUCT"
export NERVES_HUB_CERT="MY USER CERT"
export NERVES_HUB_KEY="MY USER KEY"
```

```python
from nerves_hub_client import NervesHubAPI
api = NervesHubAPI.from_env()
api.device_list()
```

## Development

```bash
poetry run pre-commit install
```

### Testing

```bash
poetry run pytest --mypy
```
