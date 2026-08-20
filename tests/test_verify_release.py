from pathlib import Path

from tools.verify_release import REQUIRED_DOCS, verify


def test_verify_release_rejects_local_artifacts_and_large_files(tmp_path: Path) -> None:
    for relative in REQUIRED_DOCS:
        path = tmp_path / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("content", encoding="utf-8")
    assert verify(tmp_path) == []
    model = tmp_path / "models" / "best.pt"; model.parent.mkdir(); model.write_bytes(b"weights")
    errors = verify(tmp_path)
    assert any("models" in error for error in errors)
    assert any("best.pt" in error for error in errors)
