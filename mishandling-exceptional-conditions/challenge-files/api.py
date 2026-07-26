from io import BytesIO
from pathlib import Path
import sqlite3
import sys

from fastapi import APIRouter, Body, Cookie, Depends, File, Header, HTTPException, Response, UploadFile
from PIL import Image

from database import (
    award_introduction_bonus,
    get_store_items,
    get_user_by_id,
    init_db,
    make_session_token,
    parse_session_token,
    purchase_item,
    search_activities,
    set_vip,
    verify_credentials,
)

# Flags/secrets live outside challenge-files.
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))
from lab_secrets import ADMIN_API_KEY, FLAGS

router = APIRouter(prefix="/api", tags=["API"])

COOKIE_NAME = "session_token"

USER_EXAMPLE = {
    "id": 7701,
    "user_id": 7701,
    "username": "ctfuser",
    "name": "Albert",
    "points": 0,
    "introduction": None,
    "vip": False,
}

LOGIN_SUCCESS_EXAMPLE = {
    "status": "ok",
    "message": "Login successful",
    "user": USER_EXAMPLE,
}

ME_EXAMPLE = {
    "user_id": 7701,
    "username": "ctfuser",
    "name": "Albert",
    "points": 0,
    "has_introduction": False,
    "vip": False,
}

ACTIVITIES_EXAMPLE = [
    {
        "id": 1,
        "title": "Trivia",
        "points": 100,
    },
    {
        "id": 3,
        "title": "Class Test",
        "points": 500,
    },
]

ADMIN_SECRETS_EXAMPLE = {
    "secret": "FLAG{REDACTED}",
}

INTRODUCE_SUCCESS_EXAMPLE = {
    "ok": True,
    "message": "Introduction saved; 10,000 points awarded",
}

STORE_ITEMS_EXAMPLE = [
    {
        "id": 1,
        "name": "Super Secret Item",
        "cost": 100000,
        "is_secret": 1,
    },
    {
        "id": 2,
        "name": "Campus Coffee",
        "cost": 50,
        "is_secret": 0,
    },
    {
        "id": 3,
        "name": "Elite University Hoodie",
        "cost": 1000,
        "is_secret": 0,
    },
]

PURCHASE_SECRET_EXAMPLE = {
    "message": "Purchased Car",
    "points": 0,
    "flag": "FLAG{REDACTED}",
}

VIP_VERIFY_EXAMPLE = {
    "message": "Badge verification complete. VIP access granted.",
}

VIP_SHOP_EXAMPLE = {
    "flag": "FLAG{REDACTED}",
    "message": "Welcome to the Elite VIP shop",
}

RESET_DATABASE_EXAMPLE = {
    "status": "ok",
    "message": "Database reset",
}


def _example(value: object) -> dict:
    """Build an OpenAPI 200 response that shows a success example in Swagger."""
    return {
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": value,
                }
            },
        }
    }


def get_current_user(session_token: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict:
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
    responses=_example(LOGIN_SUCCESS_EXAMPLE),
)
def api_login(
    response: Response,
    payload: dict = Body(example={"username": "ctfuser", "password": "ctfpassword"}),
):
    """Authenticate with username/password and set an HttpOnly session cookie."""
    user = verify_credentials(
        str(payload.get("username", "")).strip(),
        str(payload.get("password", "")),
    )
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


@router.get(
    "/me",
    summary="Get current student",
    responses=_example(ME_EXAMPLE),
)
def api_me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated student's profile summary."""
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "name": user["name"],
        "points": user["points"],
        "has_introduction": user["introduction"] is not None,
        "vip": user["vip"],
    }


# ##############################################################################
#
#   API ENDPOINTS
#   See below for API endpoints used in challenges
#
# ##############################################################################


@router.get(
    "/activities/search",
    summary="Search activities",
    responses=_example(ACTIVITIES_EXAMPLE),
)
def api_search_activities(query: str = "", user: dict = Depends(get_current_user)):
    """Search campus activities by title query string."""
    try:
        return search_activities(query)

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Activity search failed: {error}. ADMIN_API_KEY={ADMIN_API_KEY}",
        ) from error


@router.get(
    "/admin/secrets",
    summary="Read administrator secrets",
    responses=_example(ADMIN_SECRETS_EXAMPLE),
)
def api_admin_secrets(
    admin_api_key: str = Header(
        ...,
        alias="Admin-Api-Key",
        description="Admin API key required to unlock university secrets.",
    ),
    user: dict = Depends(get_current_user),
):
    """Return admin secrets when a valid Admin-Api-Key header is provided."""

    if admin_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Admin API Key")

    return {
        "secret": FLAGS["admin_secrets"]
    }


@router.post(
    "/introduce",
    summary="Submit your introduction",
    responses=_example(INTRODUCE_SUCCESS_EXAMPLE),
)
def api_introduce(
    payload: dict = Body(example={"introduction": "Hello, Elite University!"}),
    user: dict = Depends(get_current_user),
):
    """Award the one-time introduction bonus and save the introduction text."""

    result = award_introduction_bonus(user["user_id"], payload.get("introduction"))

    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get(
    "/store/items",
    summary="List University Store items",
    responses=_example(STORE_ITEMS_EXAMPLE),
)
def api_store_items(user: dict = Depends(get_current_user)):
    """Return the list of items available in the University Store."""
    return get_store_items()


@router.post(
    "/store/purchase",
    summary="Purchase a store item",
    responses=_example(PURCHASE_SECRET_EXAMPLE),
)
def api_purchase(
    payload: dict = Body(example={"item_id": 1}),
    user: dict = Depends(get_current_user),
):
    """Purchase a store item using the current student's Personal Points."""
    result = purchase_item(user["user_id"], payload.get("item_id"))

    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])

    response = {
        "message": f"Purchased {result['item']['name']}",
        "points": result["points"],
    }

    if result["item"]["is_secret"]:
        response["flag"] = FLAGS["store_item"]

    return response


@router.post(
    "/vip/verify-badge",
    summary="Verify VIP badge image",
    responses=_example(VIP_VERIFY_EXAMPLE),
)
async def api_verify_badge(
    badge: UploadFile = File(..., description="A PNG badge image"),
    user: dict = Depends(get_current_user),
):
    """Verify an uploaded VIP badge image and grant VIP access on success."""

    try:
        if not badge.filename or not badge.filename.lower().endswith(".png"):
            raise ValueError("Badge must be a .png")

        content = await badge.read()

        # Mimics API call to verify the badge
        Image.open(BytesIO(content)).verify()

        # Always denies VIP access (since the you don't have a badge)
        set_vip(user["user_id"], False) # VIP access granted

        return {"message": "Invalid Badge. VIP access denied."}
    except Exception:
        # API call failed, badge is probably valid
        set_vip(user["user_id"], True)
        
        return {"message": "Badge verification complete. VIP access granted."}


@router.get(
    "/vip/shop",
    summary="Open VIP shop",
    responses=_example(VIP_SHOP_EXAMPLE),
)
def api_vip_shop(user: dict = Depends(get_current_user)):
    """Return VIP shop contents for students with VIP membership."""
    if not user["vip"]:
        raise HTTPException(status_code=403, detail="VIP membership required")

    return {
        "flag": FLAGS["vip_shop"],
        "message": "Welcome to the Elite VIP shop",
    }


@router.post(
    "/reset-database",
    summary="Reset CTF database",
    responses=_example(RESET_DATABASE_EXAMPLE),
)
def api_reset_database(user: dict = Depends(get_current_user)):
    """Rebuild portal.db from seed.sql for challenge retries."""
    init_db()
    return {"status": "ok", "message": "Database reset"}
