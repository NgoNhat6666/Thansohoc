
from numerus.rules import SystemRules
from numerus.engine import analyze, AnalysisInput

def _smoke(system, name):
    rules = SystemRules.load(system)
    res = analyze(AnalysisInput(full_name=name, date_of_birth="1990-01-23"), rules)
    assert res["numbers"]["life_path"] in range(1, 34)

def test_vietnamese_latin():
    _smoke("vietnamese_latin", "Trần Thị Thu Hà")

def test_greek():
    _smoke("greek_isopsephy", "ΙΩΑΝΝΗΣ")

def test_hebrew():
    _smoke("hebrew_gematria", "שלום")

def test_arabic():
    _smoke("arabic_abjad", "محمد علي")
