"""
Command-line interface for ActionKit API
"""
import json
import sys
from typing import Dict, Any

import click

from . import ActionKit


# Map of CLI resource names to ActionKit class attributes
RESOURCE_MAP = {
    'users': 'Users',
    'user': 'Users',
    'orders': 'Orders',
    'order': 'Orders',
    'orderrecurring': 'OrderRecurring',
    'donationaction': 'DonationAction',
    'donationactions': 'DonationAction',
    'donations': 'DonationAction',
    'donation': 'DonationAction',
    'campaigns': 'Campaigns',
    'campaign': 'Campaigns',
    'petitions': 'Petitions',
    'petition': 'Petitions',
    'languages': 'Languages',
    'language': 'Languages',
    'lists': 'Lists',
    'list': 'Lists',
    'groups': 'Groups',
    'group': 'Groups',
    'uploads': 'Uploads',
    'upload': 'Uploads',
    'transactions': 'Transactions',
    'transaction': 'Transactions',
    'sql': 'SQL',
    'signuppages': 'SignupPages',
    'signuppage': 'SignupPages',
    'signupactions': 'SignupActions',
    'signupaction': 'SignupActions',
    'genericpages': 'GenericPages',
    'genericpage': 'GenericPages',
    'genericactions': 'GenericActions',
    'genericaction': 'GenericActions',
    'donationpages': 'DonationPages',
    'donationpage': 'DonationPages',
    'multilingualcampaigns': 'MultilingualCampaigns',
    'multilingualcampaign': 'MultilingualCampaigns',
}

# Valid HTTP methods
METHODS = ['get', 'post', 'patch', 'put', 'delete', 'search']


def parse_params(params: tuple) -> Dict[str, Any]:
    """
    Parse key=value parameters from command line.

    Examples:
        id=123 -> {'id': '123'}
        name=test status=active -> {'name': 'test', 'status': 'active'}
    """
    parsed = {}
    for param in params:
        if '=' not in param:
            click.echo(f"Error: Invalid parameter format '{param}'. Expected key=value", err=True)
            sys.exit(1)

        key, value = param.split('=', 1)

        # Try to convert to appropriate type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.lower() == 'null' or value.lower() == 'none':
            value = None
        elif value.isdigit():
            value = int(value)
        else:
            # Try to parse as float
            try:
                value = float(value)
            except ValueError:
                # Keep as string
                pass

        parsed[key] = value

    return parsed


def format_output(data: Any, format: str = 'json') -> str:
    """Format output data for display."""
    if format == 'json':
        return json.dumps(data, indent=2, default=str)
    return str(data)


@click.command()
@click.argument('args', nargs=-1, required=True)
@click.option('--hostname', envvar='ACTIONKIT_HOSTNAME', help='ActionKit hostname')
@click.option('--username', envvar='ACTIONKIT_USERNAME', help='ActionKit username')
@click.option('--password', envvar='ACTIONKIT_PASSWORD', help='ActionKit password')
@click.option('--format', '-f', default='json', type=click.Choice(['json']),
              help='Output format')
@click.option('--raw', is_flag=True, help='Output raw response without formatting')
def main(args, hostname, username, password, format, raw):
    """
    ActionKit API command-line interface.

    Usage:
        actionkit [METHOD] RESOURCE [PARAMS...]

    Examples:
        actionkit get users id=123
        actionkit users id=123              (get is default)
        actionkit search users email=test@example.com
        actionkit post users email=new@example.com first_name=John
        actionkit patch users/123 first_name=Jane
        actionkit delete users/123

    Methods:
        get, post, patch, put, delete, search

    Resources:
        users, orders, donations, campaigns, petitions, transactions, etc.

    Parameters:
        Specified as key=value pairs
        Special handling: id=N -> looks up resource by ID
    """
    if len(args) < 1:
        click.echo("Error: Must specify at least a resource", err=True)
        click.echo("Usage: actionkit [METHOD] RESOURCE [PARAMS...]", err=True)
        sys.exit(1)

    # Parse arguments
    # Determine if first arg is a method or resource
    method = 'get'
    resource = None
    params_start = 1

    if args[0].lower() in METHODS:
        method = args[0].lower()
        if len(args) < 2:
            click.echo("Error: Must specify a resource", err=True)
            sys.exit(1)
        resource = args[1]
        params_start = 2
    else:
        resource = args[0]
        params_start = 1

    # Parse parameters
    params = parse_params(args[params_start:])

    # Handle resource path (e.g., "users/123" or just "users")
    resource_parts = resource.split('/')
    resource_name = resource_parts[0].lower()
    resource_id = resource_parts[1] if len(resource_parts) > 1 else None

    # Get the resource handler - check this before connecting
    if resource_name not in RESOURCE_MAP:
        click.echo(f"Error: Unknown resource '{resource_name}'", err=True)
        click.echo(f"Available resources: {', '.join(sorted(set(RESOURCE_MAP.keys())))}", err=True)
        sys.exit(1)

    # Connect to ActionKit
    try:
        ak = ActionKit(hostname=hostname, username=username, password=password)
    except Exception as e:
        click.echo(f"Error connecting to ActionKit: {e}", err=True)
        sys.exit(1)

    handler_name = RESOURCE_MAP[resource_name]
    handler = getattr(ak, handler_name)

    try:
        result = None

        if method == 'get':
            if resource_id:
                # Get by ID from path
                result = handler.get_by_id(resource_id, **params)
            elif 'id' in params:
                # Get by ID from params
                resource_id = params.pop('id')
                result = handler.get_by_id(resource_id, **params)
            else:
                # Get with params (might be a list or single item)
                result = handler.get(**params)

        elif method == 'search':
            result = handler.search(**params)

        elif method == 'post':
            # POST creates a new resource
            result = handler.post(json=params)
            # If we got a resource_uri back, fetch the created object
            if isinstance(result, str) and result.startswith('/rest/v1/'):
                result = handler.get(result)

        elif method == 'patch':
            if resource_id:
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            elif 'id' in params:
                resource_id = params.pop('id')
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            else:
                click.echo("Error: PATCH requires a resource ID", err=True)
                sys.exit(1)

            result = handler.patch(resource_uri, params)
            # Fetch the updated object
            result = handler.get(resource_uri)

        elif method == 'put':
            if resource_id:
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            elif 'id' in params:
                resource_id = params.pop('id')
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            else:
                click.echo("Error: PUT requires a resource ID", err=True)
                sys.exit(1)

            result = handler.put(resource_uri, params)
            # Fetch the updated object
            result = handler.get(resource_uri)

        elif method == 'delete':
            if resource_id:
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            elif 'id' in params:
                resource_id = params.pop('id')
                resource_uri = handler.get_resource_uri_from_id(resource_id)
            else:
                click.echo("Error: DELETE requires a resource ID", err=True)
                sys.exit(1)

            result = handler.delete(resource_uri)
            result = {'deleted': True, 'resource_uri': resource_uri}

        # Output result
        if raw:
            click.echo(result)
        else:
            click.echo(format_output(result, format))

    except Exception as e:
        click.echo(f"Error executing {method} on {resource}: {e}", err=True)
        import traceback
        if '--debug' in sys.argv:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
