
from numerus.rules import SystemRules
from numerus.engine import analyze, AnalysisInput

def test_basic_analysis():
    rules = SystemRules.load("pythagorean")
    result = analyze(
        AnalysisInput(full_name="Nguyen Van A", date_of_birth="2000-07-15", gender=None, target_year=2025),
        rules
    )
    assert "numbers" in result
    assert result["numbers"]["life_path"] in range(1, 34)  # allow master numbers
    assert result["numbers"]["birthday"] in range(1, 34)
    assert isinstance(result["numbers"]["lo_shu"], dict)
