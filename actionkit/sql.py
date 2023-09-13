from .donationaction import DonationAction
from .httpmethods import HttpMethods


class SQL(HttpMethods):
    resource_name = 'report/run/sql'

    def __init__(self, connection):
        self.donation_action = DonationAction(connection)
        super().__init__(connection)

    def _run_query(self, query: str = '', **values: dict):
        """
        Runs an arbitrary SQL query against the ActionKit database.
        Returns the result.

        For reference see:
        https://action.wemove.eu/docs/manual/api/rest/reports.html#running-an-ad-hoc-query

        :param query: The SQL query to run.
        :param values: The values to be substituted into the query, if any.
        """
        if not query:
            raise ValueError('Query must be provided')
        return self.connection.post(
            self.resource_name, json=dict(query=query, **values)
        )

    def get_action_by_subscription_id(self, provider_subscription_id: str):
        """
        Search and return a action record with a specific provider_subscription_id custom
        action field.

        :param provider_subscription_id: The provider subscription id to search for.

        Returns the action record if found
        """
        query = """
            SELECT core_action.id AS "action_id"
            FROM core_action
            JOIN core_actionfield ON core_actionfield.parent_id = core_action.id
            JOIN core_order ON core_order.action_id = core_action.id
            WHERE core_actionfield.value = {{ provider_subscription_id }}
            GROUP BY core_action.id
        """
        response = self._run_query(
            query, provider_subscription_id=provider_subscription_id
        )
        results = response.json()
        if results:
            if len(results) > 1:
                self.logger.warning(
                    f'Found multiple action records with provider_subscription_id {provider_subscription_id}'
                )
                # Return the action data as presented by the ActionKit API
                return self.donation_action.get(results[0]['action_id'])
            return results[0]
        return None
