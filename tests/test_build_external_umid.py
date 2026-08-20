import pytest

from tools.build_external_umid import remap_line


@pytest.mark.parametrize(("source", "expected"), [
    ("0 .5 .5 .2 .2", "1 .5 .5 .2 .2"),
    ("1 .5 .5 .2 .2", "0 .5 .5 .2 .2"),
    ("2 .5 .5 .2 .2", "2 .5 .5 .2 .2"),
])
def test_remap_line_uses_vector_class_ids(source: str, expected: str) -> None:
    assert remap_line(source) == expected


def test_remap_line_rejects_unknown_class() -> None:
    with pytest.raises(ValueError, match="desconocida"):
        remap_line("3 .5 .5 .2 .2")
