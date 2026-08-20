from PIL import Image

from src.processing.preprocessing import preprocess_experimental


def test_experimental_preprocessing_preserves_original(tmp_path):
    source = tmp_path / "original.png"; output = tmp_path / "processed" / "original.png"
    Image.new("RGB", (80, 60), (100, 110, 120)).save(source)
    before = source.read_bytes()
    assert preprocess_experimental(source, output) == output
    assert source.read_bytes() == before
    assert output.is_file() and output != source
