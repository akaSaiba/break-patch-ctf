from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response
import sqlite3

from database import (
    get_classmates,
    get_exam_solutions,
    get_exams,
    get_notes_by_uuid,
    get_results_by_user_id,
    get_user_by_id,
    make_session_token,
    mass_update_user,
    parse_session_token,
    verify_credentials,
)

router = APIRouter(prefix="/api", tags=["API"])

COOKIE_NAME = "session_token"

USER_EXAMPLE = {
    "id": 5501,
    "user_id": 5501,
    "username": "ctfuser",
    "name": "Bob McBuilder",
    "bio": "First-year security engineering student.",
    "role": "student",
    "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
}

LOGIN_SUCCESS_EXAMPLE = {
    "status": "ok",
    "message": "Login successful",
    "user": USER_EXAMPLE,
}

RESULTS_EXAMPLE = [
    {
        "assignment": "Lab 1",
        "score": "92/100",
        "grade": "A-",
        "submitted": "2026-02-10",
    },
    {
        "assignment": "Lab 2",
        "score": "85/100",
        "grade": "B",
        "submitted": "2026-03-01",
    },
]

EXAMS_EXAMPLE = [
    {
        "id": 1,
        "course": "Security Engineering",
        "title": "Final Exam",
        "content": "[REDACTED]",
    }
]

EXAM_SOLUTIONS_EXAMPLE = [
    {
        "id": 1,
        "exam_id": 1,
        "title": "Final Exam Solutions",
        "solution": "A1. Horizontal = same privilege tier...\nA2. ...",
    }
]

CLASSMATES_EXAMPLE = [
    {
        "id": 1,
        "user_id": 9908,
        "name": "Harry Potter",
        "uuid": "a1b2c3d4-e5f6-7820-adcd-ef1234567890",
    },
    {
        "id": 2,
        "user_id": 3332,
        "name": "Hermione Granger",
        "uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    },
]

NOTES_EXAMPLE = [
    {
        "title": "Week 1 Notes",
        "content": "Watch Extended Security Lectures",
    }
]


def _json_example(example) -> dict:
    """Build an OpenAPI 200 response that shows a success example in Swagger."""
    return {
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": example,
                }
            },
        }
    }


def get_current_user(session_token: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    """Returns user object from session token"""
    user_id = parse_session_token(session_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session token")

    return user


@router.post(
    "/login",
    summary="Log in",
    responses=_json_example(LOGIN_SUCCESS_EXAMPLE),
)
def api_login(payload: dict, response: Response):
    """Authenticate with username/password and set an HttpOnly session cookie."""
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    user = verify_credentials(username, password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=COOKIE_NAME,
        value=make_session_token(user),
        httponly=True,
    )
    return {
        "status": "ok",
        "message": "Login successful",
        "user": user,
    }

# ##############################################################################
#
#   API ENDPOINTS
#   See below for API endpoints used in challenges
#
# ##############################################################################

@router.get(
    "/results/{user_id}",
    summary="Fetches course results for a user",
    responses=_json_example(RESULTS_EXAMPLE),
)
def api_results(user_id: int, user: dict = Depends(get_current_user)):
    """Given a user_id, fetches the course results for that user"""
    
    results = get_results_by_user_id(user_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Results not found")

    return results


@router.get(
    "/staff/exams/papers",
    summary="Fetches exam papers",
    responses=_json_example(EXAMS_EXAMPLE),
)
def api_staff_exams(user: dict = Depends(get_current_user)):
    """Return exam papers"""

    return get_exams()


@router.get(
    "/staff/exams/solutions",
    summary="Staff-only exam solution",
    responses=_json_example(EXAM_SOLUTIONS_EXAMPLE),
)
def api_staff_exam_solution(user: dict = Depends(get_current_user)):
    """Return exam solutions"""
    if user["role"] != "staff":
        raise HTTPException(status_code=403, detail="Staff only")

    return get_exam_solutions()


@router.get(
    "/classmates",
    summary="Returns a list of classmates",
    responses=_json_example(CLASSMATES_EXAMPLE),
)
def api_classmates(user: dict = Depends(get_current_user)):
    """Returns a list of classmates"""

    return get_classmates()


@router.get(
    "/notes/{uuid}",
    summary="Fetches notes for a user",
    responses=_json_example(NOTES_EXAMPLE),
)
def api_notes(uuid: str, user: dict = Depends(get_current_user)):
    """Given a uuid, fetches the notes for that user"""

    notes = get_notes_by_uuid(uuid)
    if notes is None:
        raise HTTPException(status_code=404, detail="Notes not found")

    return notes


@router.get(
    "/profile",
    summary="Get current profile",
    responses=_json_example(USER_EXAMPLE),
)
def api_get_profile(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return user


@router.put(
    "/profile",
    summary="Updates the current user's profile",
    responses=_json_example({**USER_EXAMPLE, "role": "staff"}),
)
def api_put_profile(
    payload: dict = Body(
        example={
            "name": "Bob McBuilder",
            "bio": "First-year security engineering student"
        }
    ),
    user: dict = Depends(get_current_user),
):
    """Update the current user's profile with the given payload."""
    logged_in_id = user["user_id"]

    try:
        updated = mass_update_user(logged_in_id, payload)
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=400, detail=f"Invalid profile update: {error}") from error

    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")

    return updated
