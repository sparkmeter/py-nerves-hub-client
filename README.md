# Python client for NervesHub

A thin wrapper around the NervesHub User API

See https://github.com/nerves-hub/nerves_hub_user_api for more details.

## Usage

Set up your environment

```bash
export NERVES_HUB_ORG="MY ORG"
export NERVES_HUB_PRODUCT="MY PRODUCT"
export NERVES_HUB_TOKEN="MY USER TOKEN"

# If using a self-hosted NervesHub instance (optional)
export NERVES_HUB_BASE_URL="https://my-nerveshub-domain"
export NERVES_HUB_CA_CERT="MY CA CERT"
```

```python
from nerves_hub_client import NervesHubAPI
api = NervesHubAPI.from_env()
api.device_list()
```

## Development

```bash
# Ensure linting passes before committing
poetry run pre-commit install
```

### Testing

```bash
poetry run pytest --mypy
```

### Manual lint

Linting is run before each commit if you have the pre-commit installed, but
you can run it manually with the following command.

```bash
poetry run pre-commit run
```
