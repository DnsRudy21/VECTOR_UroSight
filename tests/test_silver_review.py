from src.processing.class_normalizer import class_display_name, normalize_class_name
from tools.silver_review import presence_difference
from tools.validation_experiments import counts
from tools.select_threshold import fixed_threshold_metrics
from types import SimpleNamespace


def test_presence_qa_does_not_infer_object_counts():
    assert presence_difference('cast|eryth', {'eryth', 'cryst'}) == {
        'possibly_missed': ['cast'], 'possibly_unsupported': ['cryst'],
        'presence_consistent': False}
    assert presence_difference('', set())['presence_consistent']


def test_epithelial_nucleus_display_preserves_storage_ontology():
    assert class_display_name('epithn') == 'Núcleos epiteliales'
    assert normalize_class_name('epithn') == 'celulas_epiteliales_nucleadas'
    assert normalize_class_name('Núcleos epiteliales') == normalize_class_name('epithn')
    assert class_display_name('epith') != class_display_name('epithn')


def test_confusion_penalizes_both_real_classes():
    result = counts([{'class_id': 0, 'box': [0, 0, 10, 10]}],
                    [{'class_id': 1, 'box': [0, 0, 10, 10]}])
    assert result[0].tolist() == [0, 0, 1]
    assert result[1].tolist() == [0, 1, 0]


def test_threshold_sweep_does_not_use_max_f1_summary():
    box = SimpleNamespace(mp=.99, mr=.99, px=[0., 1.],
                          p_curve=[[.2, .8]], r_curve=[[1., 0.]])
    p, r = fixed_threshold_metrics(box, .5)
    assert p == .5 and r == .5
