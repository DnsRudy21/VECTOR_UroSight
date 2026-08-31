from tools.build_targeted_tiles import _crop_window, crop_labels


def test_crop_window_stays_inside_image() -> None:
    assert _crop_window(10, 10, 800, 600, 512) == (0, 0, 512, 512)
    assert _crop_window(790, 590, 800, 600, 512) == (288, 88, 800, 600)


def test_crop_labels_transforms_and_rejects_small_fragments() -> None:
    labels = [
        (3, 256, 256, 100, 100),
        (5, 520, 256, 40, 40),
    ]
    transformed = crop_labels(labels, (0, 0, 512, 512))
    assert transformed == ["3 0.50000000 0.50000000 0.19531250 0.19531250"]
