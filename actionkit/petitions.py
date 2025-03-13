from .httpmethods import HttpMethods


class Petitions(HttpMethods):
    resource_name = "petitionpage"

    def create(self, page, content, followup):
        page_uri = self.post(page)

        content = dict(content)
        content["page"] = page_uri
        response = self.connection.post("petitionform", json=content)
        cms_form_uri = self.get_resource_uri(response)

        followup = dict(followup)
        followup["page"] = page_uri
        response = self.connection.post("pagefollowup", json=followup)
        followup_uri = self.get_resource_uri(response)

        return (page_uri, cms_form_uri, followup_uri)

    def create_from_model(self, model, page, content, followup):
        base_page = {k: model[k] for k in ["language", "goal", "goal_type", "recognize", "allow_multiple_responses"]}
        new_page = base_page | page
        new_page["fields"] = model["fields"] | page["fields"]
        new_page["groups"] = new_page.get("groups", []) + [g["resource_uri"] for g in model["groups"]]

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
            for k in model["followup"] if k not in ["id", "page", "resource_uri", "url"]
        }
        new_followup |= followup
        uris = self.create(new_page, new_content, new_followup)

        model_form_id = self.get_resource_uri_id(model["cms_form"]["resource_uri"])
        cms_form_id = self.get_resource_uri_id(uris[1])
        form_fields = self.connection.get("userformfield", params=dict(form_id=model_form_id, form_type=333)).json().get("objects")
        for field in form_fields:
            new_field = {k: field[k] for k in field if k not in ["id", "form_id", "created_at", "updated_at", "resource_uri"]}
            new_field["form_id"] = cms_form_id
            self.connection.post("userformfield", new_field)

        return uris

    def get(self, id):
        return super().get(f"petitionpage/{id}/")

    def update(self, id, params):
        return self.patch(f"petitionpage/{id}/", params)
