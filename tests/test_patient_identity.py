from src.domain.models import StudyResult, generate_patient_id


def test_patient_id_is_generated_and_does_not_derive_from_name():
    first = generate_patient_id()
    second = generate_patient_id()
    assert first.startswith("PT-")
    assert first != second
    result = StudyResult([], patient_name="Nombre sensible")
    assert "NOMBRE" not in result.patient_id.upper()
    assert result.patient_name == "Nombre sensible"
