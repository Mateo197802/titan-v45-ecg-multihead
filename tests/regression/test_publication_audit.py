from __future__ import annotations

from pathlib import Path

from titan_v45.artifacts.publication_audit import audit_public_tree


def test_publication_audit_detects_private_paths_and_email(tmp_path: Path) -> None:
    windows_path = "C:" + "\\Users\\private\\model.pt"
    email = "researcher" + "@example.edu"
    unix_path = "/home/" + "private/model.pt"
    (tmp_path / "bad.txt").write_text(
        f"{windows_path}\n{email}\n{unix_path}",
        encoding="utf-8",
    )
    findings = audit_public_tree(tmp_path)
    kinds = {finding.kind for finding in findings}
    assert kinds == {"windows_user_path", "unix_home_path", "email"}


def test_publication_audit_ignores_git_metadata(tmp_path: Path) -> None:
    git = tmp_path / ".git"
    git.mkdir()
    (git / "config").write_text("C:" + "\\Users\\private", encoding="utf-8")
    assert audit_public_tree(tmp_path) == []
