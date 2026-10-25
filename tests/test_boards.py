from __future__ import annotations

from io import BytesIO


def test_create_and_list_boards(client) -> None:
    created = client.post("/boards", json={"name": "Anatomy", "description": "refs"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Anatomy"
    assert body["image_count"] == 0

    listed = client.get("/boards")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == body["id"]
    assert listed.json()[0]["preview_images"] == []


def test_upload_list_and_delete_image(client, fake_storage) -> None:
    board = client.post("/boards", json={"name": "Environments"}).json()
    board_id = board["id"]

    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
        b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("pixel.png", BytesIO(png_bytes), "image/png")}
    uploaded = client.post(f"/boards/{board_id}/images", files=files)
    assert uploaded.status_code == 201, uploaded.text
    image = uploaded.json()
    assert image["source_type"] == "LOCAL_UPLOAD"
    assert image["content_path"] == f"/images/{image['id']}/content"
    assert len(fake_storage.objects) == 1

    listed = client.get(f"/boards/{board_id}/images")
    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 1
    assert len(page["items"]) == 1
    assert page["items"][0]["id"] == image["id"]

    board_read = client.get(f"/boards/{board_id}").json()
    assert len(board_read["preview_images"]) == 1
    assert board_read["preview_images"][0]["id"] == image["id"]

    content = client.get(image["content_path"])
    assert content.status_code == 200
    assert content.content == png_bytes
    assert content.headers["content-type"].startswith("image/png")

    deleted = client.delete(f"/boards/{board_id}/images/{image['id']}")
    assert deleted.status_code == 204
    empty = client.get(f"/boards/{board_id}/images").json()
    assert empty["items"] == []
    assert empty["total"] == 0
    assert fake_storage.objects == {}


def test_reject_unsupported_content_type(client) -> None:
    board_id = client.post("/boards", json={"name": "X"}).json()["id"]
    files = {"file": ("notes.txt", BytesIO(b"hello"), "text/plain")}
    response = client.post(f"/boards/{board_id}/images", files=files)
    assert response.status_code == 400
