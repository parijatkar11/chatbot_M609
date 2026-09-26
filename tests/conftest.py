import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.graph import reset_graph


@pytest.fixture
def api_client():
    main.conversations.clear()
    main.approval_queue.clear()
    reset_graph()
    with TestClient(main.app) as client:
        yield client
    main.conversations.clear()
    main.approval_queue.clear()
    reset_graph()
