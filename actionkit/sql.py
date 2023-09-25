from .donationaction import DonationAction
from .httpmethods import HttpMethods


class SQL(HttpMethods):
    resource_name = 'report/run/sql'

    def __init__(self, connection):
        self.donation_action = DonationAction(connection)
        super().__init__(connection)

    def _run_query(
        self, query: str = '', refresh=False, cache_duration=600, **values: dict
    ):
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
            self.resource_name,
            json=dict(
                query=query,
                refresh=refresh,
                cache_duration=cache_duration,
                **values,
            ),
        )
