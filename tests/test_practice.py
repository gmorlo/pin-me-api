from __future__ import annotations

import uuid
from io import BytesIO

from app.core.constants import DEMO_USER_ID
from app.models.progress import PracticeProgress, ProgressStatus
from app.repositories import practice as practice_repo


PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
    b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _board_with_images(client, count: int = 3) -> str:
    board_id = client.post("/boards", json={"name": "Practice Board"}).json()["id"]
    for index in range(count):
        files = {"file": (f"img{index}.png", BytesIO(PNG), "image/png")}
        response = client.post(f"/boards/{board_id}/images", files=files)
        assert response.status_code == 201, response.text
    return board_id


def test_start_session_builds_unique_available_queue(client) -> None:
    board_id = _board_with_images(client, 4)
    created = client.post(
        "/practice/sessions",
        json={
            "board_id": board_id,
            "duration_per_image_seconds": 60,
            "image_count": 3,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "ACTIVE"
    assert body["image_count"] == 3
    assert len(body["queue"]) == 3
    ids = [item["image_id"] for item in body["queue"]]
    assert len(ids) == len(set(ids))
    assert body["current_image"] is not None
    assert body["pending_count"] == 3


def test_complete_marks_progress_skip_keeps_available(client, db_session) -> None:
    board_id = _board_with_images(client, 2)
    session = client.post(
        "/practice/sessions",
        json={
            "board_id": board_id,
            "duration_per_image_seconds": 30,
            "image_count": 2,
        },
    ).json()
    session_id = session["id"]
    first_image_id = uuid.UUID(session["current_image"]["image_id"])

    completed = client.post(
        f"/practice/sessions/{session_id}/complete",
        json={"elapsed_seconds": 12},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["completed_count"] == 1
    assert completed.json()["pending_count"] == 1

    db_session.expire_all()
    progress = (
        db_session.query(PracticeProgress)
        .filter_by(user_id=DEMO_USER_ID, image_id=first_image_id)
        .one()
    )
    assert progress.status == ProgressStatus.COMPLETED.value
    assert progress.completion_count == 1

    second_image_id = uuid.UUID(completed.json()["current_image"]["image_id"])
    skipped = client.post(
        f"/practice/sessions/{session_id}/skip",
        json={"elapsed_seconds": 5},
    )
    assert skipped.status_code == 200
    body = skipped.json()
    assert body["status"] == "FINISHED"
    assert body["skipped_count"] == 1
    assert body["completed_count"] == 1
    assert body["total_practice_seconds"] == 17

    db_session.expire_all()
    skip_progress = (
        db_session.query(PracticeProgress)
        .filter_by(user_id=DEMO_USER_ID, image_id=second_image_id)
        .one_or_none()
    )
    # Missing row or AVAILABLE both mean the image stays practiceable.
    assert skip_progress is None or skip_progress.status == ProgressStatus.AVAILABLE.value


def test_reset_restores_available_keeps_events(client, db_session) -> None:
    board_id = _board_with_images(client, 2)
    board_uuid = uuid.UUID(board_id)
    session = client.post(
        "/practice/sessions",
        json={
            "board_id": board_id,
            "duration_per_image_seconds": 30,
            "image_count": 1,
        },
    ).json()
    client.post(
        f"/practice/sessions/{session['id']}/complete",
        json={"elapsed_seconds": 10},
    )

    db_session.expire_all()
    events_before = practice_repo.count_completion_events_for_board(
        db_session, board_id=board_uuid, user_id=DEMO_USER_ID
    )
    assert events_before == 1

    reset = client.post(f"/boards/{board_id}/reset-progress")
    assert reset.status_code == 200
    assert reset.json()["reset_count"] >= 1

    db_session.expire_all()
    events_after = practice_repo.count_completion_events_for_board(
        db_session, board_id=board_uuid, user_id=DEMO_USER_ID
    )
    assert events_after == 1

    available = practice_repo.list_available_image_ids(
        db_session, board_id=board_uuid, user_id=DEMO_USER_ID
    )
    assert len(available) == 2


def test_pause_and_resume(client) -> None:
    board_id = _board_with_images(client, 1)
    session_id = client.post(
        "/practice/sessions",
        json={
            "board_id": board_id,
            "duration_per_image_seconds": 45,
            "image_count": 1,
        },
    ).json()["id"]

    paused = client.post(f"/practice/sessions/{session_id}/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "PAUSED"

    resumed = client.post(f"/practice/sessions/{session_id}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "ACTIVE"
