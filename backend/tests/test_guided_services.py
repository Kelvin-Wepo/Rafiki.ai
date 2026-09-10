"""Deep-link a frontend service card into the matching agency workflow."""

from services.agency_workflows import (
    GUIDED_SERVICES,
    clear_session,
    get_or_create_session,
    handle_message,
    start_service,
)


def teardown_function():
    # start_service always uses a fresh uuid; nothing to clean unless we reuse ids
    pass


def test_unknown_slug_raises():
    try:
        start_service("not-a-real-service")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unknown service" in str(exc)


def test_ntsa_renew_skips_menus_and_completes():
    sid, reply = start_service("ntsa-renew")
    state = get_or_create_session(sid)
    assert state.agency == "NTSA"
    assert state.service == "Renew a Driving Licence"
    assert state.step == "NTSA_RENEW_CONFIRM"
    assert state.language == "en"
    assert "Renew" in reply
    assert "eCitizen" not in reply
    assert "password" not in reply.lower()

    handle_message(sid, "yes")
    assert state.step == "NTSA_RENEW_ID"

    handle_message(sid, "12345678")
    handle_message(sid, "yes")
    handle_message(sid, "0712345678")
    assert state.awaiting_payment is True
    assert state.payment_amount == 1200
    assert state.payment_description == "NTSA Driving Licence Renewal"
    clear_session(sid)


def test_passport_apply_starts_on_name():
    sid, reply = start_service("passport-apply")
    state = get_or_create_session(sid)
    assert state.agency == "Immigration"
    assert state.service == "Apply for a Passport"
    assert state.step == "IMMIGRATION_NAME"
    assert "Passport" in reply
    assert "full name" in reply.lower()
    clear_session(sid)


def test_lost_id_completes_without_ecitizen():
    sid, reply = start_service("id-replace")
    state = get_or_create_session(sid)
    assert state.agency == "NRB"
    assert state.service == "Replace a Lost ID"
    assert "police abstract" in reply.lower()

    handle_message(sid, "Jane Wanjiku")
    handle_message(sid, "12345678")
    handle_message(sid, "OB/12/2026")
    handle_message(sid, "Nairobi")
    handle_message(sid, "0712345678")
    handle_message(sid, "0712345678")
    assert state.step == "NRB_REPLACE_CONFIRM"
    handle_message(sid, "yes")
    assert state.awaiting_payment is True
    assert state.payment_amount == 1000
    clear_session(sid)


def test_landing_slugs_all_resolve():
    landing = [
        "passport-apply",
        "ntsa-renew",
        "id-replace",
        "brs-register",
        "dci-good-conduct",
        "kra-itax",
        "land-rates",
        "agencies",
    ]
    for slug in landing:
        sid, reply = start_service(slug)
        assert reply
        state = get_or_create_session(sid)
        assert state.step != "LANGUAGE_SELECT"
        assert state.step != "ASK_DISABILITY"
        clear_session(sid)


def test_agency_menu_only_slug():
    sid, reply = start_service("ntsa")
    state = get_or_create_session(sid)
    assert state.agency == "NTSA"
    assert state.step == "NTSA_MENU"
    assert "Renew a Driving Licence" in reply
    clear_session(sid)


def test_catalog_covers_dashboard_agencies():
    for slug in ("kra", "ntsa", "brs", "dci", "immigration", "health", "huduma", "agencies"):
        assert slug in GUIDED_SERVICES
