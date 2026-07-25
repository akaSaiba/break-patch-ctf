"""Patch verification checks for Broken Access Control challenges 1–4."""

from __future__ import annotations

from typing import Any

import requests

TARGET_BASE = "http://broken-access-controls:5000"

# Hard coded constants used for each scenario
PLAYER_USER_ID = 5501
OTHER_USER_ID = 5502
OTHER_NOTES_UUID = "c3d4e5f6-a7b8-9012-cdef-123456789012"
PLAYER_NOTES_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
STAFF_USER_ID = 9999

COOKIE_NAME = "session_token"

# Helper functions
def _result(ok: bool, message: str) -> dict[str, Any]:
    return {"test_result": ok, "message": message}


def _session_for(user_id: int) -> requests.Session:
    """Mimics a logged in user's session given a user_id"""
    session = requests.Session()
    session.cookies.set(COOKIE_NAME, f"session_{user_id}")
    return session


def _get(session: requests.Session, path: str, **kwargs) -> requests.Response:
    return session.get(f"{TARGET_BASE}{path}", timeout=5, **kwargs)


def _put(session: requests.Session, path: str, payload: dict, **kwargs) -> requests.Response:
    return session.put(f"{TARGET_BASE}{path}", json=payload, timeout=5, **kwargs)


# Test functions
def test_challenge_1() -> dict[str, Any]:
    """
    Challenge 1

    Patch must block a student from reading another student's results,
    while still allowing access to their own results.
    """
    try:
        player = _session_for(PLAYER_USER_ID)

        own = _get(player, f"/api/results/{PLAYER_USER_ID}")
        if own.status_code != 200:
            return _result(
                False,
                f"Fetching own results should still work (expected 200, got {own.status_code}).",
            )

        other = _get(player, f"/api/results/{OTHER_USER_ID}")
        if other.status_code == 200:
            return _result(
                False,
                "Student can still read another student's results"
            )

        if other.status_code != 403:
            return _result(
                False,
                f"Unexpected status {other.status_code} when accessing another user's results (expected 403)"
            )

        return _result(
            True,
            f"PATCH SUCCESS",
        )
    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")


def test_challenge_2() -> dict[str, Any]:
    """
    Challenge 2

    Patch must deny students access to staff exam papers,
    while still allowing staff.
    """
    try:
        student = _session_for(PLAYER_USER_ID)
        staff = _session_for(STAFF_USER_ID)

        student_resp = _get(student, "/api/staff/exams/papers")
        if student_resp.status_code == 200:
            return _result(
                False,
                "Student can still fetch staff exam papers"
            )

        if student_resp.status_code != 403:
            return _result(
                False,
                f"Unexpected status {student_resp.status_code} for student access (expected 403)"
            )

        staff_resp = _get(staff, "/api/staff/exams/papers")
        if staff_resp.status_code != 200:
            return _result(
                False,
                f"Staff should still be able to access exam papers (expected 200, got {staff_resp.status_code}).",
            )

        return _result(
            True,
            f"PATCH SUCCESS",
        )
    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")


def test_challenge_3() -> dict[str, Any]:
    """
    Challenge 3

    Patch must block reading another user's notes by UUID,
    while still allowing access to the caller's own notes.
    """
    try:
        player = _session_for(PLAYER_USER_ID)

        own = _get(player, f"/api/notes/{PLAYER_NOTES_UUID}")
        if own.status_code != 200:
            return _result(
                False,
                f"Fetching own notes should still work (expected 200, got {own.status_code}).",
            )

        other = _get(player, f"/api/notes/{OTHER_NOTES_UUID}")
        if other.status_code == 200:
            return _result(
                False,
                "Student can still read another user's notes"
            )

        if other.status_code != 403:
            return _result(
                False,
                f"Unexpected status {other.status_code} when accessing another user's notes (expected 403)"
            )

        return _result(
            True,
            f"PATCH SUCCESS",
        )
    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")


def test_challenge_4() -> dict[str, Any]:
    """
    Challenge 4

    Patch must reject privilege escalation via a `role` field in the profile
    update payload, while still allowing normal profile edits.
    """
    try:
        player = _session_for(PLAYER_USER_ID)

        # Ensure we start from a known student role if a prior run escalated.
        _put(player, "/api/profile", {"role": "student", "name": "Bob McBuilder"})

        escalate = _put(
            player,
            "/api/profile",
            {
                "name": "Bob McBuilder",
                "bio": "First-year security engineering student.",
                "role": "staff",
            },
        )
        if escalate.status_code != 403:
            return _result(
                False,
                f"Unexpected status {escalate.status_code} on profile update (expected 403)",
            )

        profile = _get(player, "/api/profile")
        if profile.status_code != 200:
            return _result(
                False,
                f"Could not re-fetch profile after update (got {profile.status_code}).",
            )

        role = profile.json().get("role")
        if role == "staff":
            # Restore so later checks / lab use stay sane.
            _put(player, "/api/profile", {"role": "student", "name": "Bob McBuilder"})
            return _result(
                False,
                "Mass assignment still allows setting role to staff via PUT /api/profile.",
            )

        # Legitimate edit should still succeed.
        edit = _put(
            player,
            "/api/profile",
            {
                "name": "Bob McBuilder",
                "bio": "First-year security engineering student.",
            },
        )
        if edit.status_code != 200:
            return _result(
                False,
                f"Normal profile edits should still work (expected 200, got {edit.status_code}).",
            )

        # Staff-only solutions must remain protected for students.
        solutions = _get(player, "/api/staff/exams/solutions")
        if solutions.status_code == 200:
            return _result(
                False,
                "Student can access exam solutions",
            )

        return _result(
            True,
            "PATCH SUCCESS",
        )
    except requests.RequestException as error:
        return _result(False, f"FAIL: could not reach challenge app — {error}")
