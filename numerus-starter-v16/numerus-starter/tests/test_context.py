
from numerus.reporter import _match_rule, _score_rule

def test_match_simple():
    assert _match_rule({"lp":1, "ex":7}, 1,7,3,4) is True
    assert _match_rule({"lp":1, "ex":7}, 1,3,3,4) is False
    assert _match_rule({"lp":[1,10,19]}, 10,7,3,4) is True

def test_score():
    assert _score_rule({"lp":1, "ex":7}) == 4
    assert _score_rule({"lp":1, "su":2}) == 3
    assert _score_rule({"lp":1, "pe":8}) == 2
    assert _score_rule({"ex":7}) == 1
