from __future__ import annotations

from pathlib import Path

from app.services.file_service import FileService


def test_file_service_saves_to_expected_relative_path(tmp_path: Path) -> None:
    service = FileService(tmp_path)

    saved = service.save_file(
        job_id="job-123",
        original_filename="sample.png",
        content_type="image/png",
        contents=b"dummy-binary",
        extension=".png",
        width=640,
        height=480,
    )

    assert saved.relative_path.startswith("uploads/job-123/")
    assert saved.stored_filename.endswith(".png")
    assert saved.width == 640
    assert saved.height == 480

    stored_path = Path(tmp_path) / "job-123" / saved.stored_filename
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"dummy-binary"
