import io
import re

import pytest

from app.storage import TemporaryStorage


def test_saved_files_get_server_generated_uuid_names(tmp_path):
    storage = TemporaryStorage(tmp_path)
    path = storage.save(b"a,b\n1,2\n", ".csv")
    assert re.fullmatch(r"[0-9a-f]{32}\.csv", path.name)
    assert path.read_bytes() == b"a,b\n1,2\n"
    assert path.parent == tmp_path


def test_streams_are_supported_and_names_are_unique(tmp_path):
    storage = TemporaryStorage(tmp_path)
    first = storage.save(io.BytesIO(b"x"), ".joblib")
    second = storage.save(io.BytesIO(b"x"), ".joblib")
    assert first != second


@pytest.mark.parametrize("bad", ["", "csv", "../x", ".c/sv", r"..\x",".toolongextension"])
def test_user_controlled_extensions_cannot_alter_the_path(tmp_path, bad):
    with pytest.raises(ValueError):
        TemporaryStorage(tmp_path).save(b"x", bad)


def test_delete_removes_stored_file_but_not_outside_files(tmp_path):
    storage = TemporaryStorage(tmp_path / "store")
    path = storage.save(b"x", ".csv")
    storage.delete(path)
    assert not path.exists()
    outside = tmp_path / "keep.txt"
    outside.write_text("keep")
    with pytest.raises(ValueError):
        storage.delete(outside)
    assert outside.exists()
