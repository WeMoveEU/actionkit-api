from .httpmethods import HttpMethods

class MultilingualCampaigns(HttpMethods):
    """
    Multilingualcampaigns are used to represent a journey step of a campaign,
    that is a group of action pages of the same action type but in multiple languages
    """
    resource_name = "multilingualcampaign"

    @staticmethod
    def name(campaign_name: str, action_type: str) -> str:
        return f"{campaign_name}: {action_type}"

    def get_step(self, campaign_name: str, action_type: str) -> dict:
        multilangs = super().search(name= self.name(campaign_name, action_type))
        if len(multilangs) == 0:
            return None
        return multilangs[0]

    def create(self, campaign_name: str, action_type: str) -> str:
        return self.post({"name": self.name(campaign_name, action_type)})

