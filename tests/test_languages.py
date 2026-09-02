import json as json_module

import pytest
import responses

from urls import rest


@pytest.fixture
def languages(ak):
    return ak.Languages


def _lang(name, iso_code, translations=None):
    return {
        "name": name,
        "iso_code": iso_code,
        "resource_uri": rest(f"language/{iso_code}/"),
        "translations": json_module.dumps(translations or {}),
    }


@responses.activate
def test_by_code_uses_actual_iso_code_and_skips_disco(languages):
    fr = _lang("French", "fr")
    fake = _lang("Disco", "xx", {"actual_iso_code": "de"})
    responses.add(
        responses.GET,
        rest("language"),
        json={"objects": [fr, fake], "meta": {"next": None}},
        status=200,
    )
    result = languages.by_code()
    assert set(result.keys()) == {"fr"}
    assert result["fr"]["iso_code"] == "fr"


@responses.activate
def test_by_code_uses_translation_override_when_present(languages):
    workaround = _lang("Klingon (fake)", "xx", {"actual_iso_code": "tlh"})
    responses.add(
        responses.GET,
        rest("language"),
        json={"objects": [workaround], "meta": {"next": None}},
        status=200,
    )
    result = languages.by_code()
    assert "tlh" in result
    assert result["tlh"]["iso_code"] == "tlh"


@responses.activate
def test_uris_does_not_filter_disco(languages):
    """
    Unlike by_code(), uris() has no "Disco" exclusion -- pinning the
    inconsistency between the two methods.
    """
    disco = _lang("Disco", "xx", {"actual_iso_code": "de"})
    responses.add(
        responses.GET,
        rest("language"),
        json={"objects": [disco], "meta": {"next": None}},
        status=200,
    )
    result = languages.uris()
    assert result == {"de": rest("language/xx/")}
