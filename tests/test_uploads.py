import responses

from urls import rest


@responses.activate
def test_poll_gets_upload_status(ak):
    responses.add(
        responses.GET, rest("upload/1/"), json={"is_completed": True}, status=200
    )
    assert ak.Uploads.poll(rest("upload/1/")) == {"is_completed": True}


@responses.activate
def test_upload_sends_expected_multipart_fields(ak, tmp_path, monkeypatch):
    csv_file = tmp_path / "import.csv"
    csv_file.write_text("email\na@example.com\n")

    responses.add(
        responses.POST,
        rest("upload"),
        status=201,
        headers={"Location": rest("upload/1/")},
    )
    responses.add(
        responses.GET, rest("upload/1/"), json={"is_completed": True}, status=200
    )
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    ak.Uploads.upload(str(csv_file), "/rest/v1/importpage/1/")

    post_request = responses.calls[0].request
    assert post_request.headers["Content-Type"].startswith("multipart/form-data")
    body = post_request.body.decode("utf-8") if isinstance(post_request.body, bytes) else post_request.body
    assert 'name="page"' in body
    assert "/rest/v1/importpage/1/" in body
    assert 'name="upload"; filename=' in body
    assert 'name="autocreate_user_fields"' in body
    # autocreate_user_fields is sent as the literal string "false", not a bool
    assert "\r\n\r\nfalse\r\n" in body


@responses.activate
def test_upload_polls_until_is_completed(ak, tmp_path, monkeypatch):
    """
    Pins the current, unbounded polling loop -- see uploads.py:32-34. There
    is no timeout or max-attempt count in the real implementation; a stuck
    ActionKit import would hang the caller forever. This test only
    terminates because the mocked poll() sequence is finite.
    """
    csv_file = tmp_path / "import.csv"
    csv_file.write_text("email\na@example.com\n")

    responses.add(
        responses.POST,
        rest("upload"),
        status=201,
        headers={"Location": rest("upload/1/")},
    )
    poll_results = [
        {"is_completed": False},
        {"is_completed": False},
        {"is_completed": True},
    ]
    call_count = {"n": 0}

    def poll(self, upload_url):
        result = poll_results[call_count["n"]]
        call_count["n"] += 1
        return result

    monkeypatch.setattr("actionkit.uploads.Uploads.poll", poll)
    sleeps = []
    monkeypatch.setattr("time.sleep", lambda seconds: sleeps.append(seconds))

    ak.Uploads.upload(str(csv_file), "/rest/v1/importpage/1/")

    assert call_count["n"] == 3
    assert sleeps == [1, 1]
