import src.main as application


def test_main_reports_provider_configuration_error(monkeypatch):
    messages = []
    monkeypatch.setattr(application, "QApplication", lambda _args: object())
    monkeypatch.setattr(application, "build_provider", lambda: (_ for _ in ()).throw(FileNotFoundError("modelo ausente")))
    monkeypatch.setattr(application.QMessageBox, "critical", lambda _parent, title, message: messages.append((title, message)))
    assert application.main() == 2
    assert messages == [("No se pudo iniciar VECTOR UroSight", "modelo ausente")]
