import subprocess

from tools import publication_check


def repository(tmp_path, monkeypatch):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    monkeypatch.setattr(publication_check, 'ROOT', tmp_path)
    return tmp_path


def test_ignored_private_files_are_not_publication_candidates(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    (root / '.gitignore').write_text('.env\nartifacts/\n')
    (root / '.env').write_text('private configuration')
    (root / 'README.md').write_text('Public documentation')
    assert publication_check.candidate_files() == ['.gitignore', 'README.md']
    assert not publication_check.check(history=False)['findings']


def test_forced_tracked_private_file_is_rejected(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    (root / '.gitignore').write_text('.env\n')
    (root / '.env').write_text('private configuration')
    publication_check.git('add', '-f', '.env')
    assert 'unexpected-file: .env' in publication_check.check(history=False)['findings']


def test_deleted_secret_is_detected_in_history_without_value_disclosure(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    secret = 'ghp_' + 'A' * 36
    (root / 'README.md').write_text(secret)
    publication_check.git('add', 'README.md')
    publication_check.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
    (root / 'README.md').write_text('Clean current content')
    result = publication_check.check()
    assert any('github-token: history:' in item for item in result['findings'])
    assert secret not in str(result)


def test_unexpected_binary_and_oversized_document_are_rejected(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    (root / 'model.pt').write_bytes(b'checkpoint')
    (root / 'README.md').write_bytes(b'a' * (5 * 1024 * 1024 + 1))
    findings = publication_check.check(history=False)['findings']
    assert 'unexpected-file: model.pt' in findings
    assert 'over-5-MiB: README.md' in findings
