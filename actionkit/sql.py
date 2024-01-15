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

    def run_query(self, query: str = '', **values: dict):
        """
        Runs an arbitrary SQL query against the ActionKit database.
        Returns the json results as a list.

        For reference see:
        https://action.wemove.eu/docs/manual/api/rest/reports.html#running-an-ad-hoc-query
        """
        response = self._run_query(query, **values)
        return response.json()

    def fetch_transaction_id_by_trans_id(self, trans_id: str) -> dict:
        """
        Fetches a transaction record id by associated trans_id. Currently unsupported functionality
        by ActionKit API transaction endpoint queries, so we need to run a custom query. If it gets
        supported in the future, we can do the same with a get?trans_id=<value> query on the
        transaction endpoint.
        """
        query = """
            SELECT id
            FROM core_transaction
            WHERE trans_id = {{ trans_id }}
        """
        results = self.run_query(query, trans_id=trans_id)
        if results:
            if len(results) > 1:
                self.connection.logger.warning(
                    f'More than 1 result found for trans_id {trans_id} in transaction table'
                )
            return results[0][0]
        return None
