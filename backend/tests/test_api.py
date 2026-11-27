import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import httpx2
import pytest
from fastapi.testclient import TestClient
from openai import AsyncOpenAI
from pydantic import SecretStr
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel
from sqlalchemy import create_engine, update

from app.accounts.models import EmailChallenge
from app.agent.workflow import build_agent
from app.core.config import Settings
from app.core.db import utc_now
from app.main import create_app

API = "/api/v1"
ORIGIN = "http://127.0.0.1:5173"
PASSWORD = "a-development-only-password"
BIRTH = {"year": 2022, "month": 8, "day": 28, "birth_time": "01:50"}


@pytest.fixture
def client(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if url is None:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    app = create_app(
        Settings(
            database_url=url,
            ai_api_key=None,
            ai_model="",
            development_admin_password=None,
            smtp_host="smtp.example.com",
            smtp_sender="auth@example.com",
            auth_code_secret=SecretStr("x" * 40),
            wechat_app_secret=SecretStr("wechat-test-only"),
        )
    )
    app.state.test_mail = {}

    async def capture_email(settings, email, purpose, code):
        app.state.test_mail[email, purpose] = code

    monkeypatch.setattr("app.accounts.verification.deliver_code", capture_email)
    with TestClient(app) as test_client:
        assert test_client.get("/api/health/ready").status_code == 200
        yield test_client


def request_code(client, email, purpose, headers=None):
    endpoint = "email/code" if purpose == "bind_email" else "send-code"
    response = client.post(f"{API}/auth/{endpoint}", headers=headers, json={"email": email})
    assert response.status_code == 200, response.text
    assert response.json() == {"cooldown": 30, "expires_in": 300}
    return client.app.state.test_mail[email.casefold(), purpose]


def session_headers(response):
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def register_user(client, username=None):
    result = client.post(
        f"{API}/auth/register",
        json={
            "username": username or f"user_{uuid4().hex[:12]}",
            "password": PASSWORD,
            "transport": "bearer",
        },
    )
    assert result.status_code == 201, result.text
    return result


def test_eight_character_passwords_and_reserved_admin_name(client):
    route = f"{API}/auth"
    payload = {
        "username": f"eight_{uuid4().hex[:12]}",
        "password": "pass2026",
        "transport": "bearer",
    }
    assert (
        client.post(f"{route}/register", json={**payload, "password": "pass202"}).status_code == 422
    )
    reserved = client.post(f"{route}/register", json={**payload, "username": "ADMIN"})
    assert reserved.status_code == 409
    member = client.post(f"{route}/register", json=payload)
    assert member.status_code == 201
    assert member.json()["account"]["is_admin"] is False
    headers = session_headers(member)
    update = {"current_password": payload["password"], "password": "next2026"}
    assert (
        client.put(
            f"{route}/credentials", headers=headers, json={**update, "password": "next202"}
        ).status_code
        == 422
    )
    assert client.put(f"{route}/credentials", headers=headers, json=update).status_code == 200
    assert (
        client.post(
            f"{route}/login",
            json={"identifier": payload["username"], "password": update["password"]},
        ).status_code
        == 200
    )


def test_development_admin_is_seeded_once_and_disabled_in_production(client):
    route = f"{API}/auth"
    config = client.app.state.settings
    password = "devtest8"
    login = {"identifier": "admin", "password": password, "transport": "bearer"}
    first = config.model_copy(
        update={"environment": "development", "development_admin_password": SecretStr(password)}
    )
    with TestClient(create_app(first)) as local:
        entered = local.post(f"{route}/login", json=login)
        assert entered.status_code == 200, entered.text
        account = entered.json()["account"]
        assert account["is_admin"] is True and account["is_guest"] is False
        assert local.get(f"{route}/session", headers=session_headers(entered)).json() == account

    restarted = first.model_copy(
        update={"development_admin_password": SecretStr("different-password")}
    )
    with TestClient(create_app(restarted)) as local:
        assert local.post(f"{route}/login", json=login).json()["account"]["id"] == account["id"]

    production = first.model_copy(update={"environment": "production", "cookie_secure": True})
    with TestClient(create_app(production)) as deployed:
        assert deployed.post(f"{route}/login", json=login).status_code == 403
        assert deployed.get(f"{route}/session", headers=session_headers(entered)).status_code == 401


def bind_member_email(client, headers, email):
    code = request_code(client, email, "bind_email", headers)
    response = client.post(
        f"{API}/auth/email/bind",
        headers=headers,
        json={
            "email": email,
            "code": code,
            "current_password": PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return response


def headers_for(client, *, email=None):
    if email is None:
        response = client.post(f"{API}/auth/guest", json={"transport": "bearer"})
    else:
        response = register_user(client)
        bind_member_email(client, session_headers(response), email)
    assert response.status_code == 201, response.text
    return session_headers(response)


def create_reading(client, kind, payload, headers, key=None):
    return client.post(
        f"{API}/readings/{kind}",
        json=payload,
        headers={**headers, "Idempotency-Key": key or uuid4().hex},
    )


def event_payloads(response):
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")
    return [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]


def test_guest_cookie_upgrade_keeps_readings_and_requires_same_origin(client):
    guest = client.post(f"{API}/auth/guest", json={})
    assert guest.status_code == 201
    assert "HttpOnly" in guest.headers["set-cookie"]
    assert create_reading(client, "tarot", {}, {}).status_code == 403
    request = create_reading(client, "tarot", {}, {"Origin": ORIGIN})
    assert request.status_code == 200
    identifier = request.json()["id"]
    username = f"user_{uuid4().hex[:12]}"
    result = client.post(
        f"{API}/auth/register",
        headers={"Origin": ORIGIN},
        json={
            "username": username,
            "password": PASSWORD,
            "display_name": "测试",
        },
    )
    assert result.status_code == 201, result.text
    assert result.json()["account"]["id"] == guest.json()["account"]["id"]
    assert (
        client.patch(
            f"{API}/readings/{identifier}", headers={"Origin": ORIGIN}, json={"saved": True}
        ).json()["saved"]
        is True
    )
    assert (
        client.get(f"{API}/readings/{identifier}", headers=headers_for(client)).status_code == 404
    )
    assert client.delete(f"{API}/auth/session", headers={"Origin": ORIGIN}).status_code == 204
    assert client.get(f"{API}/auth/session").status_code == 401
    assert (
        client.post(
            f"{API}/auth/login",
            json={"identifier": username, "password": PASSWORD, "transport": "bearer"},
        ).status_code
        == 200
    )


def test_registration_username_and_email_login_share_account_and_limits(client):
    route = f"{API}/auth"
    username = f"User_{uuid4().hex[:12]}"
    email = f"{uuid4().hex}@example.com"
    registered = register_user(client, username)
    member = registered.json()["account"]
    headers = session_headers(registered)
    assert member["username"] == username.lower() and member["email"] is None
    assert not member["is_guest"] and member["password_set"]
    assert not client.app.state.test_mail
    duplicate = client.post(
        f"{route}/register", json={"username": username.upper(), "password": PASSWORD}
    )
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "username_in_use"
    assert (
        client.post(
            f"{route}/register", json={"username": "a@b.com", "password": PASSWORD}
        ).status_code
        == 422
    )
    duplicate_owner = session_headers(register_user(client))
    logged_in = client.post(
        f"{route}/login", json={"identifier": username.upper(), "password": PASSWORD}
    )
    assert logged_in.status_code == 200 and logged_in.json()["account"]["id"] == member["id"]
    before_bind = client.post(f"{route}/login", json={"identifier": email, "password": PASSWORD})
    assert before_bind.status_code == 401
    old_cookie = logged_in.headers["set-cookie"].split(";", 1)[0]
    bound = bind_member_email(client, headers, email)
    assert bound.json()["id"] == member["id"]
    assert bound.json()["username"] == username.lower()
    assert (
        client.post(
            f"{route}/email/code", headers=duplicate_owner, json={"email": email}
        ).status_code
        == 409
    )

    def sign_in(identifier, password):
        return client.post(
            f"{route}/login",
            json={"identifier": identifier, "password": password, "transport": "bearer"},
        )

    assert sign_in(email, PASSWORD).json()["account"]["id"] == member["id"]
    for identifier in [username, email, username.upper(), email.upper(), username]:
        assert sign_in(identifier, "incorrect-password").status_code == 401
    assert sign_in(email, PASSWORD).status_code == 429
    assert (
        client.post(f"{route}/login-code", json={"email": email, "code": "001200"}).status_code
        == 404
    )

    code = request_code(client, email, "reset_password")
    updated = {"email": email, "code": code, "password": "newkey89"}
    assert client.post(f"{route}/reset-password", json=updated).status_code == 204
    assert client.get(f"{route}/session").status_code == 401
    assert client.get(f"{route}/session", headers={"Cookie": old_cookie}).status_code == 401
    assert client.get(f"{route}/session", headers=headers).status_code == 401
    assert client.post(f"{route}/reset-password", json=updated).status_code == 401
    assert sign_in(email, PASSWORD).status_code == 401
    assert sign_in(username, updated["password"]).status_code == 200
    assert sign_in(email, updated["password"]).status_code == 200


def test_binding_code_scope_attempt_limit_and_expiration(client):
    route = f"{API}/auth"
    owner = session_headers(register_user(client))
    other = session_headers(register_user(client))
    email = f"{uuid4().hex}@example.com"
    code = request_code(client, email, "bind_email", owner)
    payload = {"email": email, "code": code, "current_password": PASSWORD}
    assert (
        client.post(f"{route}/email/code", json={"email": email}, headers=owner).status_code == 429
    )
    assert client.post(f"{route}/email/bind", json=payload, headers=other).status_code == 401
    assert (
        client.post(f"{route}/reset-password", json={**payload, "password": PASSWORD}).status_code
        == 401
    )
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(4):
        assert (
            client.post(
                f"{route}/email/bind", json={**payload, "code": wrong}, headers=owner
            ).status_code
            == 401
        )
    assert client.post(f"{route}/email/bind", json=payload, headers=owner).status_code == 429
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.begin() as connection:
            connection.execute(
                update(EmailChallenge)
                .where(EmailChallenge.email == email)
                .values(expires_at=utc_now() - timedelta(seconds=1))
            )
    finally:
        engine.dispose()
    expired = client.post(f"{route}/email/bind", json=payload, headers=owner)
    assert expired.status_code == 401 and expired.json()["error"]["code"] == "code_expired"


def test_existing_email_account_can_add_username_without_replacing_password(client):
    from argon2 import PasswordHasher

    from app.accounts.models import Account

    user_id = uuid4()
    email = f"{uuid4().hex}@example.com"
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    try:
        with engine.begin() as connection:
            connection.execute(
                Account.__table__.insert().values(
                    id=user_id,
                    email=email,
                    password_hash=PasswordHasher().hash(PASSWORD),
                    display_name="原邮箱账号",
                )
            )
    finally:
        engine.dispose()

    route = f"{API}/auth"
    result = client.post(
        f"{route}/login", json={"email": email, "password": PASSWORD, "transport": "bearer"}
    )
    assert result.status_code == 200 and result.json()["account"]["id"] == str(user_id)
    assert result.json()["account"]["username"] is None
    username = f"legacy_{uuid4().hex[:12]}"
    configured = client.put(
        f"{route}/credentials",
        json={
            "username": username,
            "current_password": PASSWORD,
        },
        headers=session_headers(result),
    )
    assert configured.status_code == 200
    assert configured.json()["account"]["id"] == str(user_id)
    assert client.get(f"{route}/session", headers=session_headers(result)).status_code == 401
    assert (
        client.post(
            f"{route}/login", json={"identifier": username, "password": PASSWORD}
        ).status_code
        == 200
    )


def test_wechat_sign_in_session_rotation_and_explicit_binding(client, monkeypatch):
    open_id = f"wx-test-{uuid4().hex}"
    codes = {
        "visitor-code": open_id,
        "set-password": open_id,
        "other-wechat": open_id + "-other",
        "recover-password": open_id,
        "repeat-code": open_id,
        "conflict-code": open_id,
        "bind-code": open_id + "-second",
        "after-bind-code": open_id + "-second",
    }

    async def exchange(request):
        assert request.method == "GET" and request.url.host == "api.weixin.qq.com"
        assert request.url.path == "/sns/jscode2session"
        assert request.url.params["appid"] == "wx99173f0f5cf30a60"
        assert request.url.params["grant_type"] == "authorization_code"
        code = request.url.params["js_code"]
        if code not in codes:
            return httpx2.Response(200, json={"errcode": 40029})
        return httpx2.Response(200, json={"openid": codes.pop(code), "session_key": "test-only"})

    async_client = httpx2.AsyncClient
    monkeypatch.setattr(
        "app.accounts.wechat.httpx2.AsyncClient",
        lambda **options: async_client(transport=httpx2.MockTransport(exchange), **options),
    )
    route = f"{API}/auth"
    guest = client.post(f"{route}/guest", json={"transport": "bearer"})
    previous = session_headers(guest)
    reading = create_reading(client, "tarot", {}, previous).json()["id"]
    wechat = client.post(f"{route}/wechat", headers=previous, json={"code": "visitor-code"})
    assert wechat.status_code == 200, wechat.text
    wechat_user = wechat.json()["account"]
    assert wechat_user["id"] == guest.json()["account"]["id"]
    assert (
        wechat_user["wechat_linked"]
        and not wechat_user["is_guest"]
        and wechat_user["email"] is None
    )
    assert client.get(f"{route}/session", headers=previous).status_code == 401
    assert (
        client.get(f"{API}/readings/{reading}", headers=session_headers(wechat)).status_code == 200
    )
    repeat = client.post(f"{route}/wechat", json={"code": "repeat-code"})
    assert repeat.json()["account"]["id"] == wechat_user["id"]
    assert client.post(f"{route}/wechat", json={"code": "repeat-code"}).status_code == 401

    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    assert (
        client.post(
            f"{route}/wechat/bind", headers=owner, json={"code": "conflict-code"}
        ).status_code
        == 409
    )
    bound = client.post(f"{route}/wechat/bind", headers=owner, json={"code": "bind-code"})
    assert bound.status_code == 200 and bound.json()["wechat_linked"]
    assert (
        client.post(f"{route}/wechat", json={"code": "after-bind-code"}).json()["account"]["id"]
        == bound.json()["id"]
    )

    username = f"wxuser_{uuid4().hex[:12]}"
    payload = {"username": username, "password": PASSWORD}
    assert (
        client.post(f"{route}/register", json=payload, headers=session_headers(wechat)).status_code
        == 409
    )
    assert (
        client.put(
            f"{route}/credentials",
            json={**payload, "wechat_code": "other-wechat"},
            headers=session_headers(wechat),
        ).status_code
        == 403
    )
    upgraded = client.put(
        f"{route}/credentials",
        json={**payload, "wechat_code": "set-password"},
        headers=session_headers(wechat),
    )
    assert upgraded.status_code == 200, upgraded.text
    assert upgraded.json()["account"]["id"] == wechat_user["id"]
    assert (
        upgraded.json()["account"]["wechat_linked"] and upgraded.json()["account"]["email"] is None
    )
    assert client.get(f"{route}/session", headers=session_headers(wechat)).status_code == 401

    web = client.post(f"{route}/login", json={"identifier": username, "password": PASSWORD})
    assert web.status_code == 200 and web.json()["account"]["id"] == wechat_user["id"]
    assert client.get(f"{API}/readings/{reading}").status_code == 200
    assert (
        client.post(
            f"{API}/ai/conversations",
            headers={"Origin": ORIGIN},
            json={"role": "tarot", "reading_id": reading},
        ).status_code
        == 201
    )
    new_password = "wechat-recovery-test-password"
    reset = client.put(
        f"{route}/credentials",
        json={"password": new_password, "wechat_code": "recover-password"},
        headers=session_headers(upgraded),
    )
    assert reset.status_code == 200
    assert client.get(f"{route}/session").status_code == 401
    assert (
        client.post(
            f"{route}/login", json={"identifier": username, "password": new_password}
        ).status_code
        == 200
    )


def test_core_endpoints_and_concurrent_idempotency(client):
    owner = headers_for(client)
    payload = {"spread_id": "timeline", "question": "接下来怎么做？"}
    key = uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as pool:
        requests = [
            pool.submit(create_reading, client, "tarot", payload, owner, key) for _ in range(2)
        ]
        first, second = [response.result() for response in requests]
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert create_reading(client, "tarot", {}, owner, key).status_code == 409
    assert len(client.get(f"{API}/tarot/cards").json()) == 78
    assert len(client.get(f"{API}/zodiac").json()) == 12
    assert client.get(f"{API}/fortune/aries").json()["content_kind"] == "base_editorial"
    assert create_reading(client, "oracle", {}, owner).json()["result"]["verse"]
    assert (
        create_reading(client, "liuyao", {"lines": [7] * 6}, owner).json()["result"]["hexagram"]
        == "乾"
    )
    assert (
        create_reading(client, "bazi", {"birth": BIRTH}, owner).json()["result"]["day_master"]
        == "癸"
    )
    first_daily = client.post(f"{API}/readings/daily-tarot", headers=owner)
    assert first_daily.json() == client.post(f"{API}/readings/daily-tarot", headers=owner).json()


def test_private_profile_snapshot_and_journal(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    other = headers_for(client, email=f"{uuid4().hex}@example.com")
    profile = client.post(
        f"{API}/me/profiles", headers=owner, json={"name": "本人", "birth": BIRTH}
    )
    assert profile.status_code == 201
    profile_id = profile.json()["id"]
    key = uuid4().hex
    assert create_reading(client, "bazi", {"profile_id": profile_id}, other).status_code == 404
    reading = create_reading(client, "bazi", {"profile_id": profile_id}, owner, key).json()
    assert client.delete(f"{API}/me/profiles/{profile_id}", headers=owner).status_code == 204
    assert create_reading(client, "bazi", {"profile_id": profile_id}, owner, key).json() == reading
    payload = {"title": "今日", "body": "记录", "reading_id": reading["id"]}
    target = f"{API}/me/journal/2026-11-26"
    assert client.put(target, headers=other, json=payload).status_code == 404
    assert client.put(target, headers=owner, json=payload).status_code == 200
    assert client.get(f"{API}/me/journal", headers=other).json() == []


def test_agent_history_role_scope_and_request_bound_execution(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    other = headers_for(client, email=f"{uuid4().hex}@example.com")
    reading_id = create_reading(client, "tarot", {}, owner).json()["id"]
    anchor = f"{API}/ai/conversations"
    payload = {"role": "tarot", "reading_id": reading_id}
    assert (
        client.post(anchor, json={**payload, "role": "diviner"}, headers=owner).status_code == 422
    )
    assert client.post(anchor, json=payload, headers=other).status_code == 404
    first = client.post(anchor, json=payload, headers=owner).json()["id"]
    second = client.post(anchor, json=payload, headers=owner).json()["id"]
    assert first != second
    first_turns = f"{anchor}/{first}/turns"
    second_turns = f"{anchor}/{second}/turns"
    send = {"client_message_id": str(uuid4()), "text": "这张牌的牌位如何解读？", "task": "reading"}
    assert client.post(first_turns, json=send, headers=owner).status_code == 503

    unsupported = client.post(anchor, json={"role": "tarot"}, headers=owner).json()["id"]
    ask = client.post(f"{anchor}/{unsupported}/turns", json=send, headers=owner)
    assert event_payloads(ask)[0]["reply"]["needs_input"] is True

    invoked = []
    client.app.state.agent = build_agent(AsyncOpenAI(api_key="unit-testing"), "test-model")

    def model(messages, info):
        invoked.append(1)
        snapshot = next(
            (
                part.content
                for msg in messages
                for part in msg.parts
                if isinstance(part, ToolReturnPart) and part.tool_name == "read_snapshot"
            ),
            None,
        )
        if snapshot is None:
            return ModelResponse(
                parts=[
                    ToolCallPart("read_snapshot", {}),
                    ToolCallPart("read_reference", {"source_id": "tarot-positions"}),
                ]
            )
        assert snapshot["source_id"] == reading_id
        assert any(
            isinstance(part, ToolReturnPart)
            and part.tool_name == "read_reference"
            and part.content.get("source_id") == "tarot-positions"
            for message in messages
            for part in message.parts
        )
        return ModelResponse(
            parts=[
                ToolCallPart(
                    info.output_tools[0].name,
                    {
                        "text": "根据这次牌面，先明确你最关心的问题。",
                        "source_ids": [reading_id, "tarot-positions"],
                    },
                )
            ]
        )

    with client.app.state.agent.override(model=FunctionModel(model)):
        assert client.get(first_turns, headers=owner).json() == []
        assert invoked == []
        response = client.post(first_turns, json=send, headers=owner)
        started, completed = event_payloads(response)
        assert started["status"] == "running"
        assert completed["status"] == "complete", completed
        assert completed["reply"]["citations"][0]["id"] == reading_id
        assert completed["reply"]["citations"][1]["id"] == "tarot-positions"
        assert client.get(first_turns, headers=owner).json() == [completed]
        assert client.get(first_turns, headers=other).status_code == 404
        assert client.get(second_turns, headers=owner).json() == []
        assert event_payloads(client.post(first_turns, json=send, headers=owner)) == [completed]
        assert len(invoked) == 2


def test_account_details_notes_and_revocable_share(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    other = headers_for(client, email=f"{uuid4().hex}@example.com")
    assert (
        client.put(
            f"{API}/me",
            headers=owner,
            json={"display_name": "新昵称", "details": {"bio": "个人介绍"}},
        ).json()["details"]["bio"]
        == "个人介绍"
    )
    item = create_reading(
        client,
        "tarot",
        {
            "question": "此处是私人问题",
            "positions": [4],
        },
        owner,
    ).json()
    assert (
        create_reading(
            client,
            "tarot",
            {
                "spread_id": "timeline",
                "positions": [2, 2, 2],
            },
            owner,
        ).status_code
        == 422
    )
    path = f"{API}/readings/{item['id']}"
    assert (
        client.put(path, headers=owner, json={"note": "私人笔记", "saved": True}).json()["note"]
        == "私人笔记"
    )
    assert client.put(path, headers=other, json={"note": "修改"}).status_code == 404
    share = client.post(f"{API}/shares", json={"reading_id": item["id"]}, headers=owner)
    assert share.status_code == 201, share.text
    url = f"{API}/shares/{share.json()['id']}"
    public = client.get(url)
    assert public.status_code == 200
    assert item["result"]["cards"][0]["name"] in public.text
    assert "此处是私人问题" not in public.text and "私人笔记" not in public.text
    assert client.delete(url, headers=other).status_code == 204
    assert client.get(url).status_code == 200
    assert client.delete(url, headers=owner).status_code == 204
    assert client.get(url).status_code == 404


def test_real_natal_is_saved_and_can_be_bound_to_astrologer(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    reading = create_reading(
        client,
        "astro",
        {
            "birth": BIRTH,
            "latitude": 30.2741,
            "longitude": 120.1551,
            "house_system": "placidus",
        },
        owner,
    )
    assert reading.status_code == 200, reading.text
    assert len(reading.json()["result"]["cusps"]) == 12
    reading_id = reading.json()["id"]
    conversations = f"{API}/ai/conversations"
    created = client.post(
        conversations, json={"role": "astrologer", "reading_id": reading_id}, headers=owner
    )
    assert created.status_code == 201, created.text
    path = f"{conversations}/{created.json()['id']}"
    renamed = client.put(path, headers=owner, json={"title": "本命盘解读"})
    assert renamed.json()["reading_id"] == reading_id
    assert client.get(path, headers=owner).json()["title"] == "本命盘解读"
    assert client.put(path, headers=owner, json={"reading_id": None}).json()["reading_id"] is None


def test_login_hands_off_one_owned_guest_reading(client):
    email = f"{uuid4().hex}@example.com"
    other = headers_for(client, email=email)
    guest = headers_for(client)
    inherited = create_reading(client, "tarot", {}, guest).json()["id"]
    untouched = create_reading(client, "oracle", {}, guest).json()["id"]
    path = f"{API}/readings/{inherited}"
    denied = client.post(
        f"{API}/auth/login",
        headers=guest,
        json={
            "email": email,
            "password": "wrong-password",
            "transport": "bearer",
            "carry_reading_id": inherited,
        },
    )
    assert denied.status_code == 401
    assert client.get(path, headers=guest).status_code == 200
    result = client.post(
        f"{API}/auth/login",
        headers=guest,
        json={
            "email": email,
            "password": PASSWORD,
            "transport": "bearer",
            "carry_reading_id": inherited,
        },
    )
    assert result.status_code == 200 and result.json()["handoff_reading_id"] == inherited
    assert client.get(path, headers=other).status_code == 200
    assert client.get(path, headers=guest).status_code == 404
    assert client.get(f"{API}/readings/{untouched}", headers=guest).status_code == 200


def test_light_readings_and_dream_privacy(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    other = headers_for(client)
    dice = create_reading(client, "dice", {}, owner).json()
    assert 1 <= dice["result"]["house"] <= 12
    answer = create_reading(client, "book", {}, owner).json()["result"]["answer"]
    second = create_reading(client, "book", {"previous_answer": answer}, owner)
    assert second.json()["result"]["answer"] != answer
    dream = create_reading(client, "dream", {"text": "私密梦境测试", "mood": "好奇"}, owner).json()
    assert dream["result"]["mood"] == "好奇"
    assert client.get(f"{API}/readings/{dream['id']}", headers=other).status_code == 404
    share = client.post(f"{API}/shares", json={"reading_id": dream["id"]}, headers=owner).json()
    assert "私密梦境测试" not in client.get(f"{API}/shares/{share['id']}").text


def test_report_is_bound_to_actual_bazi_and_keeps_snapshot(client):
    owner = headers_for(client, email=f"{uuid4().hex}@example.com")
    other = headers_for(client, email=f"{uuid4().hex}@example.com")
    reading = create_reading(client, "bazi", {"birth": BIRTH}, owner).json()
    source = {"template": "bazi", "reading_id": reading["id"]}
    options = {**owner, "Idempotency-Key": uuid4().hex}
    first = client.post(f"{API}/reports", json=source, headers=options)
    assert first.status_code == 200, first.text
    report = first.json()
    assert "年柱：壬寅" in report["sections"][1]["content"]
    assert "时柱：癸丑" in report["sections"][1]["content"]
    assert client.post(f"{API}/reports", json=source, headers=options).json() == report
    path = f"{API}/reports/{report['id']}"
    assert client.get(path, headers=other).status_code == 404
    assert client.delete(f"{API}/readings/{reading['id']}", headers=owner).status_code == 204
    snapshot = client.get(path, headers=owner).json()
    assert snapshot["reading_id"] is None
    assert snapshot["sections"] == report["sections"]
