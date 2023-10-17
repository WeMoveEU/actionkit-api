import json

from .httpmethods import HttpMethods


class Languages(HttpMethods):
    resource_name = "language"

    def _actual_iso_code(self, language):
        """
        ActionKit does not support all the languages we want, and does not let us add new languages.
        As a workaround, we use one of their supported languages that we will never use, and fake its name.
        The actual iso code of the language is stored in a translation string `actual_iso_code`.
        This class pretends to its users that the language code is the desired one
        """
        translations = json.loads(language["translations"])
        return translations.get("actual_iso_code", language["iso_code"])

    def by_code(self):
        langs = self.search()
        # Robotic dogs has 2 languages with same code...
        result = {}
        for l in langs:
            if l["name"] != "Disco":
                actual_iso_code = self._actual_iso_code(l)
                l["iso_code"] = actual_iso_code
                result[actual_iso_code] = l
        return result

    def uris(self):
        langs = self.search()
        return dict(map(lambda l: (self._actual_iso_code(l), l["resource_uri"]), langs))
