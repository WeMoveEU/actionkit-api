from .httpmethods import HttpMethods


class Campaigns(HttpMethods):
    """
    Campaigns are not a built-in AK resource but a WeMove concept.
    This class embeds the WeMove-specific logic common to Campaign manipulation
    """

    resource_name = "signuppage"

    def list(self) -> dict:
        "Return a dictonary mapping campaign ids to campaign names"
        field_resp = self.connection.get("allowedpagefield/campaign")
        choices = field_resp.json().get("choices")
        return dict((int(c[0]), c[1]) for c in choices)

    def create(self, name: str, campaign_type: str, **params) -> str:
        "Create a signup page representing a WeMove campaign"
        fields = dict(params.get("fields", {}))
        fields["campaign_type"] = campaign_type
        for p in ["lead_campaigner", "topic"]:
            if p in params:
                fields[p] = params[p]
        title = params.get("title", name)

        # Create the campaign page
        campaign_uri = self.post({"name": name, "title": title, "fields": fields})

        # Point it to itself
        campaign_id = self.connection.get_resource_uri_id(campaign_uri)
        self.patch(f"signuppage/{campaign_id}", {"fields": {"campaign": campaign_id}})

        # Add campaign option to custom fields
        camp_options = (
            self.connection.get("allowedpagefield/campaign").json().get("field_choices")
        )
        camp_options += f"\n{campaign_id}={name}"
        self.connection.patch(
            "allowedpagefield/campaign", {"field_choices": camp_options}
        )
        self.connection.patch(
            "allowedmailingfield/campaign", {"field_choices": camp_options}
        )

        return campaign_uri
