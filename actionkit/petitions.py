from .httpmethods import HttpMethods


class Petitions(HttpMethods):
    resource_name = "petitionpage"

    def create(self, page, content, followup):
        page_uri = self.post(page)

        content = dict(content)
        content["page"] = page_uri
        self.connection.post("petitionform", json=content)

        followup = dict(followup)
        followup["page"] = page_uri
        self.connection.post("pagefollowup", json=followup)

        return page_uri

    def create_from_model(self, model, page, content, followup):
        new_page = dict(page)
        new_page["fields"] = model["fields"] | page["fields"]

        new_content = {
            k: model["cms_form"][k]
            for k in [
                "about_text",
                "statement_leadin",
                "statement_text",
                "templateset",
                "thank_you_text",
            ]
        }
        new_content |= content

        new_followup = {
            k: model["followup"][k]
            for k in [
                "twitter_message",
                "share_description",
                "email_body",
                "email_from_line",
                "email_subject",
                "email_wrapper",
            ]
        }
        new_followup |= followup
        return self.create(new_page, new_content, new_followup)

    def get(self, id):
        return super().get(f"petitionpage/{id}/")

    def update(self, id, params):
        return self.patch(f"petitionpage/{id}/", params)
