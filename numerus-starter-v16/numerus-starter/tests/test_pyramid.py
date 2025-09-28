
from numerus.rules import SystemRules
from numerus.engine import analyze, AnalysisInput

def test_pyramid_present():
    rules = SystemRules.load("pythagorean")
    res = analyze(AnalysisInput(full_name="Nguyen Van A", date_of_birth="1990-01-23"), rules)
    assert "life_pyramid" in res["numbers"]
    assert "pinnacles_detailed" in res["numbers"]
