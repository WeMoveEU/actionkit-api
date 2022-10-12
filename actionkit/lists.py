class Lists:
    def __init__(self, connection):
        self.connection = connection

    def get_or_create(self, list_name):
        """Find or create a list."""
        connection = self.connection

        lists = connection.get(f"list/?name={list_name}")

        if lists["meta"]["total_count"] == 0:
            # sigh, terrible design. second request to get the object we just created. bad past aaron.
            return connection.get(connection.post("list/", {"name": list_name}))

        return lists["objects"][0]

    def all(self):
        return self.connection.get("list/")["objects"]
