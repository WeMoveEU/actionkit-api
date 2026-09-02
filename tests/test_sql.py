import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def sql(ak):
    return ak.SQL


def test_run_report_requires_report_name(sql):
    with pytest.raises(ValueError):
        sql.run_report("")


@responses.activate
def test_run_report_posts_to_report_name_path_and_returns_json(sql):
    responses.add(
        responses.POST,
        rest("report/run/my_report"),
        json={"results": [1, 2, 3]},
        status=200,
    )
    assert sql.run_report("my_report", extra="x") == {"results": [1, 2, 3]}
    assert json_module.loads(responses.calls[0].request.body) == {"extra": "x"}


def test_run_query_requires_query(sql):
    with pytest.raises(ValueError):
        sql.run_query("")


@responses.activate
def test_run_query_posts_query_with_defaults_and_returns_json(sql):
    responses.add(
        responses.POST, rest("report/run/sql"), json=[[1], [2]], status=200
    )
    result = sql.run_query("SELECT 1")
    assert result == [[1], [2]]
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {
        "query": "SELECT 1",
        "refresh": False,
        "cache_duration": 600,
    }


@responses.activate
def test_fetch_transaction_id_by_trans_id_returns_first_column_of_first_row(sql):
    responses.add(
        responses.POST, rest("report/run/sql"), json=[[42]], status=200
    )
    assert sql.fetch_transaction_id_by_trans_id("tx1") == 42


@responses.activate
def test_fetch_transaction_id_by_trans_id_no_results_returns_none(sql):
    responses.add(responses.POST, rest("report/run/sql"), json=[], status=200)
    assert sql.fetch_transaction_id_by_trans_id("tx1") is None


@responses.activate
def test_fetch_signup_action_ids_flattens_rows(sql):
    responses.add(
        responses.POST, rest("report/run/sql"), json=[[1], [2], [3]], status=200
    )
    assert sql.fetch_signup_action_ids(page_id=10, user_id=20) == [1, 2, 3]
    body = json_module.loads(responses.calls[0].request.body)
    assert body["page_id"] == 10
    assert body["user_id"] == 20
    assert body["cache_duration"] == 1
