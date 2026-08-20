from src.interpretation.rule_engine import interpret

def test_rule_engine_is_orientative():
    text = " ".join(interpret({"eritrocitos": 15, "leucocitos": 12}, 2)).lower()
    assert "diagnóstico" in text
    assert "orientativa" in text


def test_rule_engine_covers_all_use_classes():
    text = " ".join(interpret({
        "eritrocitos": 1, "leucocitos": 1, "celulas_epiteliales": 1,
        "celulas_epiteliales_nucleadas": 1, "cristales": 1,
        "cilindros": 1, "levaduras_hongos": 1,
    }, 1)).lower()
    for term in ("eritrocitos", "leucocitos", "epiteliales", "núcleos epiteliales", "cristales", "cilindros", "hongos o levaduras"):
        assert term in text
