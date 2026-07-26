"""Patch verification checks for Mishandling of Exceptional Conditions challenges 1–3."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import requests

TARGET_BASE = "http://mishandling-exceptional-conditions:5001"

PLAYER_USER_ID = 7701
COOKIE_NAME = "session_token"
ADMIN_API_KEY = "ELITE-ADMIN-KEY-7f3a9c2e"


def _result(ok: bool, message: str) -> dict[str, Any]:
    return {"test_result": ok, "message": message}


def _session_for(user_id: int) -> requests.Session:
    """Mimics a logged in user's session given a user_id."""
    session = requests.Session()
    session.cookies.set(COOKIE_NAME, f"session_{user_id}")
    return session


def _get(session: requests.Session, path: str, **kwargs) -> requests.Response:
    return session.get(f"{TARGET_BASE}{path}", timeout=5, **kwargs)


def _post(session: requests.Session, path: str, **kwargs) -> requests.Response:
    return session.post(f"{TARGET_BASE}{path}", timeout=5, **kwargs)


def _reset(session: requests.Session) -> None:
    _post(session, "/api/reset-database")


def test_challenge_1() -> dict[str, Any]:
    """
    Challenge 1

    Patch must return HTTP 400 on malformed search queries and must not leak
    the admin API key. Normal searches should still work.
    """
    try:
        player = _session_for(PLAYER_USER_ID)

        normal_query = _get(player, "/api/activities/search", params={"query": "Trivia"})
        if normal_query.status_code != 200:
            return _result(
                False,
                f"Normal activity search should still work (expected 200, got {normal_query.status_code}).",
            )

        broken_query = _get(player, "/api/activities/search", params={"query": "'"})
        body = broken_query.text

        if ADMIN_API_KEY in body:
            return _result(
                False,
                "Malformed search still leaks the admin API key in the error response.",
            )

        return _result(True, "GOOD JOB!")

    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")


def test_challenge_2() -> dict[str, Any]:
    """
    Challenge 2

    Patch must not keep awarded points when introduction saving fails
    (e.g. JSON Array payload), and should return HTTP 400. A valid
    introduction should still award the one-time 10,000 point bonus.
    """
    try:
        player = _session_for(PLAYER_USER_ID)
        _reset(player)

        before = _get(player, "/api/me")
        if before.status_code != 200:
            return _result(
                False,
                f"Test script could not read profile (got {before.status_code}).",
            )
        points_before = before.json().get("points", 0)

        # Test non-string payload: vulnerable code awards points then crashes while saving.
        bad = _post(
            player,
            "/api/introduce",
            json={"introduction": ["not", "a", "string"]},
        )

        after_bad = _get(player, "/api/me")
        if after_bad.status_code != 200:
            _reset(player)
            return _result(False, "Could not read profile after bad introduction.")

        points_after_bad = after_bad.json().get("points", 0)
        has_intro = after_bad.json().get("has_introduction", False)

        if points_after_bad != points_before:
            _reset(player)
            return _result(
                False,
                "Partial transaction still awards points when introduction saving fails.",
            )

        if has_intro:
            _reset(player)
            return _result(
                False,
                "Introduction should not be saved when the payload is invalid.",
            )

        if bad.status_code != 400:
            _reset(player)
            return _result(
                False,
                f"Invalid introduction should return 400 (got {bad.status_code}).",
            )

        good = _post(
            player,
            "/api/introduce",
            json={"introduction": "Welcome to the Classroom of the Elite!"},
        )

        if good.status_code != 200:
            _reset(player)
            return _result(
                False,
                f"Valid introduction should still succeed (expected 200, got {good.status_code}).",
            )

        after_good = _get(player, "/api/me")
        points_after_good = after_good.json().get("points", 0)

        if points_after_good != points_before + 10000:
            _reset(player)
            return _result(
                False,
                f"Valid introduction should award 10,000 points "
                f"(expected {points_before + 10000}, got {points_after_good}).",
            )

        _reset(player)
        return _result(True, "GOOD JOB!")
        
    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")


def test_challenge_3() -> dict[str, Any]:
    """
    Challenge 3

    Patch must deny VIP and return HTTP 400 when badge processing fails (fail closed).
    """
    try:
        player = _session_for(PLAYER_USER_ID)
        _reset(player)

        fake = BytesIO(b"this is not an image")
        bad = _post(
            player,
            "/api/vip/verify-badge",
            files={"badge": ("badge.png", fake, "image/png")},
        )

        me = _get(player, "/api/me")
        if me.status_code != 200:
            _reset(player)
            return _result(False, "Could not read profile after badge upload.")

        if me.json().get("vip"):
            _reset(player)
            return _result(
                False,
                "Fail-open still grants VIP after invalid badge processing.",
            )

        if bad.status_code != 400:
            _reset(player)
            return _result(
                False,
                f"Invalid badge upload should return 400 (got {bad.status_code}).",
            )

        shop = _get(player, "/api/vip/shop")
        if shop.status_code == 200:
            _reset(player)
            return _result(
                False,
                "VIP shop should remain blocked after a failed badge upload.",
            )

        _reset(player)
        return _result(True, "PATCH SUCCESS")

    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")
