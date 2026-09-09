import responses

from teams_backup.graph import GraphClient, GraphError, chat_path


@responses.activate
def test_follows_next_link():
    first = "https://graph.microsoft.com/v1.0/me/chats?$top=50"
    second = "https://graph.microsoft.com/v1.0/me/chats?$skiptoken=opaque"
    responses.get(first, json={"value": [{"id": "1"}], "@odata.nextLink": second})
    responses.get(second, json={"value": [{"id": "2"}]})

    values, pages = GraphClient("token").get_all("/me/chats?$top=50")

    assert [item["id"] for item in values] == ["1", "2"]
    assert len(pages) == 2


@responses.activate
def test_reports_graph_error_without_response_body_leak():
    responses.get(
        "https://graph.microsoft.com/v1.0/me",
        status=403,
        json={"error": {"message": "Forbidden", "innerError": {"request-id": "abc"}}},
    )

    try:
        GraphClient("token").get_object("/me")
    except GraphError as error:
        assert error.status_code == 403
        assert "abc" in str(error)
    else:
        raise AssertionError("GraphError was not raised")


def test_encodes_chat_id():
    assert chat_path("19:a/b@thread.v2", "messages") == "/me/chats/19%3Aa%2Fb%40thread.v2/messages"


def test_rejects_external_next_link():
    try:
        GraphClient._url("https://example.com/steal")
    except ValueError as error:
        assert "Refusing" in str(error)
    else:
        raise AssertionError("Unsafe URL was accepted")
