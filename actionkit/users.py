import re

from .httpmethods import HttpMethods


class Users(HttpMethods):
    resource_name = "user"

    def get_by_email(self, email):
        users = self.search(email=email)
        if len(users) == 0:
            return None
        else:
            return users[0]

    def create(self, user):
        return self.post(user)

    def update(self, path, user):
        return self.patch(path, user)

    def uri(self, id=None):
        return f"{self.resource_name}/{id or ''}"

    def id(self, uri):
        m = re.search(f"/{self.resource_name}/(\d+)", uri)
        if m:
            return m[1]
        else:
            raise Exception(f"{uri} is not a user URI")

    def get_by_akid(self, akid, limited=True):
        """
        Returns user info for a given akid.
        If limited is False, all of the user's data is returned
        """
        match = re.match(r'^\.(?P<user_id>\d+)\..+$', akid)
        if match:
            user = self.get(self.uri(match.group('user_id')))
            if limited:
                return {k: user[k] for k in ['first_name', 'last_name', 'email']}
            return user
        raise ValueError(f"Invalid akid: {akid}")
