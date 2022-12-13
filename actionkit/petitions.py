class Petitions:
    def __init__(self, connection):
        self.connection = connection

    def create(self, page, content):
        page_uri = self.connection.post("petitionpage", page)
        content = dict(content)
        content["page"] = page_uri
        self.connection.post("petitionform", content)
        return page_uri

    def create_from_model(self, model, page, content):
        new_page = dict(page)
        new_page["fields"] = model["fields"] | page["fields"]
        new_content = {k: model["cms_form"][k] for k in ["about_text", "statement_leadin", "statement_text", "templateset", "thank_you_text"]}
        new_content |= content
        return self.create(new_page, new_content)

    def get(self, id):
        return self.connection.get(f"petitionpage/{id}/")

    def update(self, id, params):
        return self.connection.patch(f"petitionpage/{id}/", params)
