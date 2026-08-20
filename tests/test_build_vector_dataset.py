from tools.build_vector_dataset import select_records


def test_select_records_keeps_test_copy_and_excludes_unreadable() -> None:
    rows = [
        {"stem": "train_copy", "splits": "train", "sha256": "same", "readable": "True"},
        {"stem": "test_copy", "splits": "test", "sha256": "same", "readable": "True"},
        {"stem": "bad", "splits": "train", "sha256": "", "readable": "False"},
    ]
    selected, excluded = select_records(rows)
    assert [row["stem"] for row in selected] == ["test_copy"]
    assert {row["reason"] for row in excluded} == {"exact_duplicate", "unreadable_image"}
    assert next(row for row in excluded if row["reason"] == "exact_duplicate")["kept_split"] == "test"
