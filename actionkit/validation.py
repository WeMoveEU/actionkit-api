import json
from datetime import datetime


def validate_datetime_is_timezone_aware(dt: datetime) -> None:
    """
    Simple validation to ensure that the datetime is timezone aware.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f"Datetime {dt} must be timezone aware.")


# A custom exception class to wrap valiadation errors from server responses


class ValidationError(Exception):
    def __init__(self, response_text):
        """
         Wraps a response from the server in a custom exception.
         Example response_text:
        {
         "signuppage": {
             "name": ["A page with this short name already exists (it may be a hidden page)."]
             }
         }
        """
        response = json.loads(response_text)
        self.error_dict = response

        self.errors = list(response.values())

    def __getitem__(self, field):
        if field in self.error_dict:
            return self.error_dict[field]
        else:
            return []
