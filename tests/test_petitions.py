import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def petitions(ak):
    return ak.Petitions


# --- get() -- overridden, incompatible signature ---------------------------


@responses.activate
def test_get_by_id_hardcodes_petitionpage_path(petitions):
    """
    Petitions.get(id) overrides HttpMethods.get(resource_uri=None, *args,
    **params) with an incompatible signature: positional-only `id`, no
    query-param support, and it hardcodes "petitionpage/{id}/" rather than
    using self.resource_name (which happens to also be "petitionpage" here,
    but that's coincidence, not delegation).
    """
    responses.add(responses.GET, rest("petitionpage/1/"), json={"id": 1}, status=200)
    assert petitions.get(1) == {"id": 1}


def test_get_with_resource_uri_kwarg_breaks_the_override(petitions):
    """
    The base class's `get(resource_uri=..., **params)` call shape is valid
    on HttpMethods but not on this override -- Petitions.get(self, id) has
    no `resource_uri` parameter, so calling it the way the base class
    documents its contract raises TypeError. A Liskov-substitution break:
    code written against HttpMethods.get's signature cannot safely call
    Petitions.get.
    """
    with pytest.raises(TypeError):
        petitions.get(resource_uri=rest("petitionpage/1/"))


# --- update() ------------------------------------------------------------


@responses.activate
def test_update_patches_petitionpage_path(petitions):
    responses.add(responses.PATCH, rest("petitionpage/1/"), status=200)
    assert petitions.update(1, {"title": "New title"}) is True
    body = json_module.loads(responses.calls[0].request.body)
    assert body == {"title": "New title"}


# --- create() ------------------------------------------------------------


@responses.activate
def test_create_posts_page_form_and_followup_in_order(petitions):
    responses.add(
        responses.POST,
        rest("petitionpage"),
        status=201,
        headers={"Location": rest("petitionpage/1/")},
    )
    responses.add(
        responses.POST,
        rest("petitionform"),
        status=201,
        headers={"Location": rest("petitionform/1/")},
    )
    responses.add(
        responses.POST,
        rest("pagefollowup"),
        status=201,
        headers={"Location": rest("pagefollowup/1/")},
    )

    page_uri, form_uri, followup_uri = petitions.create(
        page={"name": "test-page"},
        content={"statement_text": "Sign this"},
        followup={"thank_you_text": "Thanks!"},
    )

    assert page_uri == rest("petitionpage/1/")
    assert form_uri == rest("petitionform/1/")
    assert followup_uri == rest("pagefollowup/1/")

    assert [c.request.url.rsplit("?", 1)[0] for c in responses.calls] == [
        rest("petitionpage"),
        rest("petitionform"),
        rest("pagefollowup"),
    ]

    form_body = json_module.loads(responses.calls[1].request.body)
    assert form_body == {"statement_text": "Sign this", "page": rest("petitionpage/1/")}

    followup_body = json_module.loads(responses.calls[2].request.body)
    assert followup_body == {"thank_you_text": "Thanks!", "page": rest("petitionpage/1/")}


# --- create_from_model() --------------------------------------------------


@responses.activate
def test_create_from_model_merges_and_copies_form_fields(petitions):
    model = {
        "language": "en",
        "goal": 100,
        "goal_type": "signatures",
        "recognize": True,
        "allow_multiple_responses": False,
        "fields": {"model_field": "1"},
        "groups": [{"resource_uri": rest("usergroup/1/")}],
        "cms_form": {
            "resource_uri": rest("petitionform/9/"),
            "about_text": "About",
            "statement_leadin": "Leadin",
            "statement_text": "Statement",
            "templateset": "default",
            "thank_you_text": "Thanks",
        },
        "followup": {
            "id": 99,
            "page": rest("petitionpage/9/"),
            "resource_uri": rest("pagefollowup/9/"),
            "url": "https://example.com/thanks",
            "thank_you_text": "Old thanks",
        },
    }
    page = {"name": "new-page", "fields": {"page_field": "2"}}
    content = {"about_text": "Overridden about"}
    followup = {"thank_you_text": "New thanks"}

    responses.add(
        responses.POST,
        rest("petitionpage"),
        status=201,
        headers={"Location": rest("petitionpage/2/")},
    )
    responses.add(
        responses.POST,
        rest("petitionform"),
        status=201,
        headers={"Location": rest("petitionform/2/")},
    )
    responses.add(
        responses.POST,
        rest("pagefollowup"),
        status=201,
        headers={"Location": rest("pagefollowup/2/")},
    )
    responses.add(
        responses.GET,
        rest("userformfield"),
        json={"objects": [
            {
                "id": 1,
                "form_id": 9,
                "created_at": "x",
                "updated_at": "x",
                "resource_uri": rest("userformfield/1/"),
                "label": "Email",
            }
        ]},
        status=200,
    )
    responses.add(responses.POST, rest("userformfield"), status=201)

    uris = petitions.create_from_model(model, page, content, followup)
    assert uris == (
        rest("petitionpage/2/"),
        rest("petitionform/2/"),
        rest("pagefollowup/2/"),
    )

    page_body = json_module.loads(responses.calls[0].request.body)
    assert page_body["fields"] == {"model_field": "1", "page_field": "2"}
    assert page_body["groups"] == [rest("usergroup/1/")]

    content_body = json_module.loads(responses.calls[1].request.body)
    assert content_body["about_text"] == "Overridden about"
    assert content_body["statement_text"] == "Statement"

    followup_body = json_module.loads(responses.calls[2].request.body)
    assert followup_body["thank_you_text"] == "New thanks"
    assert "id" not in followup_body and "resource_uri" not in followup_body

    field_body = json_module.loads(responses.calls[4].request.body)
    assert field_body["label"] == "Email"
    assert field_body["form_id"] == "2"
    assert "id" not in field_body and "created_at" not in field_body
