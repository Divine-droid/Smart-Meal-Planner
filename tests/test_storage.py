from services import storage


def test_json_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    storage.save_json("x.json", {"a": 1})
    assert storage.load_json("x.json") == {"a": 1}


def test_missing_file_returns_default(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    assert storage.load_json("nope.json", default=[]) == []
