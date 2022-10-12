class Lists:
    def __init__(self, connection):
        self.connection = connection

    def get_or_create(self, list_name):
        """Find or create a list."""
        connection = self.connection

        response = connection.session.get(f"list/?name={list_name}")

        response.raise_for_status()
        lists = response.json()

        if lists["meta"]["total_count"] == 0:
            # create the list
            response = connection.post("list/", {"name": list_name})
            response.raise_for_status()

            # ok, load the new list
            response = connection.session.get(response.headers["Location"])
            response.raise_for_status()

            return response.json()

        return lists["objects"][0]

    def all(self):
        return self.connection.get("list/")["objects"]

