# ActionKit CLI Usage Guide

The ActionKit CLI provides a simple, predictable command-line interface for interacting with the ActionKit REST API.

## Installation

```bash
pip install -e .
```

## Authentication

Set environment variables:

```bash
export ACTIONKIT_HOSTNAME=your-hostname.actionkit.com
export ACTIONKIT_USERNAME=your-username
export ACTIONKIT_PASSWORD=your-password
```

Or use `.envrc` with direnv (recommended):

```bash
export ACTIONKIT_HOSTNAME=your-hostname.actionkit.com
export ACTIONKIT_USERNAME=your-username
export ACTIONKIT_PASSWORD=your-password
```

Alternatively, pass credentials via CLI options:

```bash
actionkit --hostname example.actionkit.com --username user --password pass users id=123
```

## Command Structure

```
actionkit [METHOD] RESOURCE [PARAMS...]
```

- **METHOD**: Optional HTTP method (get, post, patch, put, delete, search). Defaults to `get`.
- **RESOURCE**: The ActionKit resource type (users, orders, donations, etc.)
- **PARAMS**: Key-value pairs in the format `key=value`

## Available Resources

- `users` / `user`
- `orders` / `order`
- `donations` / `donationaction` / `donationactions`
- `campaigns` / `campaign`
- `petitions` / `petition`
- `transactions` / `transaction`
- `orderrecurring`
- `languages` / `language`
- `lists` / `list`
- `groups` / `group`
- `uploads` / `upload`
- `signuppages` / `signuppage`
- `signupactions` / `signupaction`
- `donationpages` / `donationpage`
- `genericpages` / `genericpage`
- `genericactions` / `genericaction`
- `multilingualcampaigns` / `multilingualcampaign`
- `sql`

## Examples

### GET Operations

```bash
# Get a user by ID (method defaults to 'get')
actionkit users id=123

# Explicit GET
actionkit get users id=123

# Alternative syntax with ID in path
actionkit users/123

# Get with additional parameters
actionkit users id=123 limit=10
```

### SEARCH Operations

```bash
# Search users by email
actionkit search users email=test@example.com

# Search with multiple parameters
actionkit search orders status=completed limit=50

# Search donations
actionkit search donations page=donate-page
```

### POST Operations (Create)

```bash
# Create a new user
actionkit post users email=newuser@example.com first_name=John last_name=Doe

# The CLI will automatically fetch and display the created resource
```

### PATCH Operations (Update)

```bash
# Update a user by ID in path
actionkit patch users/123 first_name=Jane

# Update using id parameter
actionkit patch users id=123 last_name=Smith

# The CLI will automatically fetch and display the updated resource
```

### PUT Operations (Full Update)

```bash
# Full update of a resource
actionkit put users/123 email=updated@example.com first_name=Jane last_name=Doe
```

### DELETE Operations

```bash
# Delete by ID in path
actionkit delete users/123

# Delete using id parameter
actionkit delete users id=123
```

## Parameter Types

The CLI automatically converts parameter values to appropriate types:

```bash
# Integers
actionkit users id=123                    # 123 as int

# Booleans
actionkit users active=true               # true as boolean
actionkit users archived=false            # false as boolean

# Null values
actionkit users middle_name=null          # null/None

# Floats
actionkit orders amount=25.50             # 25.50 as float

# Strings
actionkit users name="John Doe"           # String (quotes optional)
```

## Output Options

```bash
# Default JSON output (pretty-printed)
actionkit users id=123

# Raw output without formatting
actionkit --raw users id=123

# Specify format explicitly
actionkit --format json users id=123
```

## Error Handling

The CLI provides helpful error messages:

```bash
# Unknown resource
$ actionkit fakeresource id=1
Error: Unknown resource 'fakeresource'
Available resources: campaign, campaigns, donation, ...

# Missing parameters
$ actionkit patch users
Error: PATCH requires a resource ID

# Connection errors
$ actionkit users id=123
Error connecting to ActionKit: Oops, I couldn't find login information...
```

## Common Workflows

### Finding a user and updating their information

```bash
# Search for user
actionkit search users email=user@example.com

# Update user (using ID from search results)
actionkit patch users/456 phone=555-1234
```

### Listing recent donations

```bash
# Search donations with filters
actionkit search donations created_at__gte=2024-01-01 limit=100
```

### Checking order details

```bash
# Get specific order
actionkit orders id=789

# Search orders by status
actionkit search orders status=completed
```

## Tips

1. **Use tab completion**: Most shells support command completion after installing the package
2. **Combine with jq**: Pipe output to `jq` for advanced JSON processing
   ```bash
   actionkit users id=123 | jq '.email'
   ```
3. **Save credentials**: Use `.envrc` with direnv to automatically load credentials per directory
4. **Check available resources**: Run `actionkit fakeresource` to see the full list of available resources
