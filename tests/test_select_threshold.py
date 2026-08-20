from tools.select_threshold import f1, select


def test_select_threshold_uses_f1_and_deterministic_tie_breakers():
    rows = [
        {"threshold": .25, "precision": .5, "recall": .8, "f1": f1(.5, .8)},
        {"threshold": .35, "precision": .7, "recall": .7, "f1": f1(.7, .7)},
        {"threshold": .50, "precision": .8, "recall": .5, "f1": f1(.8, .5)},
    ]
    assert select(rows)["threshold"] == .35
