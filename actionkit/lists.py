from .httpmethods import HttpMethods


class Lists(HttpMethods):
    resource_name = "list"

    def get_or_create(self, list_name, notes=None):
        """Find or create a list."""
        lists = self.get(name=list_name)

        if lists["meta"]["total_count"] == 0:
            # sigh, terrible design. second request to get the object we just created. bad past aaron.
            return self.get(self.post({"name": list_name, "notes": notes}))

        return lists["objects"][0]

    def all(self):
        return self.get()["objects"]
