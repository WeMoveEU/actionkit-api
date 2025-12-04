# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python client library for the ActionKit REST API, used internally by WeMove. It provides a clean interface for interacting with ActionKit resources like donations, users, campaigns, petitions, and more.

## Package Information

- **Package name**: `actionkit` (version 0.3.5)
- **Dependencies**: `requests`, `requests-toolbelt`
- **Distribution**: Published to WeMove's internal GitLab PyPI repository

## Development Commands

```bash
# Install in development mode
pip install -e .

# Build the package
python setup.py sdist bdist_wheel

# Upload to GitLab (requires ~/.pypirc configuration)
python3 -m twine upload --verbose --repository gitlab dist/*

# Run tests
python -m unittest discover tests
```

## Command-Line Interface

The package includes a CLI tool for interacting with the ActionKit API:

```bash
# General syntax
actionkit [METHOD] RESOURCE [PARAMS...]

# Examples
actionkit users id=123                    # Get user by ID (default method)
actionkit get users id=123                # Explicit GET
actionkit search users email=test@example.com
actionkit post users email=new@example.com first_name=John
actionkit patch users/123 first_name=Jane
actionkit delete users/123

# Other resources
actionkit orders id=456
actionkit donations id=789
actionkit search campaigns name=climate
```

Authentication is handled via environment variables (`ACTIONKIT_USERNAME`, `ACTIONKIT_PASSWORD`, `ACTIONKIT_HOSTNAME`) or CLI options (`--hostname`, `--username`, `--password`).

## Architecture

### Connection and Authentication

The library uses a connection-based architecture:

1. **Connection class** (`actionkit/connection.py`): Manages HTTPS sessions with the ActionKit API
   - Handles authentication via HTTP Basic Auth
   - Implements automatic retry logic for flaky API responses (retries on 500 errors with exponential backoff)
   - Provides `get()`, `post()`, `patch()`, `put()`, `delete()` methods
   - Normalizes API paths (handles absolute URLs, API paths, or relative paths)

2. **Authentication**: Uses environment variables or explicit parameters:
   - `ACTIONKIT_USERNAME`
   - `ACTIONKIT_PASSWORD`
   - `ACTIONKIT_HOSTNAME`

### Resource Classes

All resource classes inherit from `HttpMethods` base class (`actionkit/httpmethods.py`), which provides:
- Standard CRUD operations: `get()`, `post()`, `patch()`, `put()`, `delete()`, `search()`
- Resource URI manipulation utilities
- Automatic pagination handling in `search()` method

Each resource class must define a `resource_name` property (e.g., `"user"`, `"donationaction"`, `"petitionpage"`).

### Main Entry Points

**High-level API** (`actionkit/__init__.py`):
```python
import actionkit
ak = actionkit.ActionKit(hostname, username, password)
# Or use environment variables:
ak = actionkit.ActionKit()
```

The `ActionKit` class exposes all resource endpoints as attributes:
- `ak.Users`, `ak.DonationAction`, `ak.Orders`, `ak.Campaigns`, etc.

**Low-level connection** (for direct API access):
```python
connection = actionkit.connect(hostname, username, password)
response = connection.get("/rest/v1/user/123/")
```

### Key Resource Classes

- **DonationAction** (`donationaction.py`): Most complex resource with specialized methods
  - `push()`: Create new donations via the donationpush endpoint
  - `set_push_status()`: Update donation/order/transaction statuses
  - Status wrappers: `set_push_status_completed()`, `set_push_status_failed()`, `set_push_status_pending()`, `set_push_status_incomplete()`
  - Recurring donation support via `recurring_id` parameter
  - `extract_resource_uris()`: Helper to get order/transaction URIs from donation data

- **Users** (`users.py`): User management
  - `get_by_email()`: Search users by email
  - `get_by_akid()`: Retrieve user by ActionKit ID (with HMAC verification)

- **Petitions** (`petitions.py`): Petition page creation
  - `create()`: Create petition with form and followup
  - `create_from_model()`: Clone petition from existing template

- **Campaigns** (`campaigns.py`): WeMove-specific campaign logic
  - Uses signuppage resource but adds WeMove conventions
  - `create()`: Creates campaign page and updates field choices

### Validation and Error Handling

- **ValidationError** (`validation.py`): Custom exception for API validation errors
- **AKID verification** (`utils.py`): HMAC-based verification using `ACTIONKIT_SECRET_KEY`
- **HTTPError handling**: Most methods catch and re-raise with additional context

### Utilities

- `utils.py`: Datetime conversion helpers, AKID verification
- `validation.py`: Timezone-aware datetime validation, custom ValidationError

## Common Patterns

### Creating a donation
```python
ak = actionkit.ActionKit()
response = ak.DonationAction.push(
    email="user@example.com",
    first_name="John",
    last_name="Doe",
    country="US",
    postal="12345",
    amount=Decimal("25.00"),
    currency="USD",
    page="donate-page",
    payment_account="/rest/v1/paymentaccount/1/",
    recurring_id="sub_123"  # Optional for recurring
)
```

### Updating donation status
```python
# Using response data directly
action = response.json()
ak.DonationAction.set_push_status_completed(
    donationaction_data=action,
    trans_id="ch_123456"
)

# Or using resource_uri
ak.DonationAction.set_push_status_failed(
    resource_uri="/rest/v1/donationaction/12345/",
    failure_message="Card declined"
)
```

### Searching and pagination
```python
# Returns all users matching criteria (auto-paginates)
users = ak.Users.search(country="US", limit=100)
```

## Testing

Tests are in `tests/` directory. Currently minimal test coverage (one test file for path handling).

To run tests:
```bash
python -m unittest discover tests
```

## Publishing Workflow

See `README.txt` for detailed instructions on publishing to GitLab PyPI repository (project ID: 62).
