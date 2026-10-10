from ai_reviewer.main import ReviewCommandLine


def test_missing_article(tmp_path, capsys):
    assert ReviewCommandLine().run([str(tmp_path / "missing.docx"), str(tmp_path / "out")]) == 1
    assert capsys.readouterr().err.startswith("error: ")
    assert not (tmp_path / "out").exists()
