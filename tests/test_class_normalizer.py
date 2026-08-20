from src.processing.class_normalizer import normalize_class_name

def test_normalizes_common_aliases():
    assert normalize_class_name("RBC") == "eritrocitos"
    assert normalize_class_name("eryth") == "eritrocitos"
    assert normalize_class_name("WBC") == "leucocitos"
    assert normalize_class_name("pus") == "leucocitos"
    assert normalize_class_name("ep") == "celulas_epiteliales"
