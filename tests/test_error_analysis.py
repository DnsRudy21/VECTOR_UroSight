from tools.error_analysis import iou, match_detections


def test_iou_and_matching_distinguish_errors() -> None:
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1
    truth = [{"class_id": 0, "box": (0, 0, 10, 10)}, {"class_id": 1, "box": (20, 20, 30, 30)}]
    predictions = [{"class_id": 0, "box": (0, 0, 10, 10)}, {"class_id": 2, "box": (20, 20, 30, 30)}, {"class_id": 0, "box": (40, 40, 50, 50)}]
    result = match_detections(truth, predictions)
    assert result["true_positives"] == [(0, 0)]
    assert result["misclassifications"] == [(1, 1)]
    assert result["false_positives"] == [2]
    assert result["false_negatives"] == []
