from __future__ import annotations

from app.ratings.ttt_adapter import TTTAdapter, build_rating_provider


def test_ttt_adapter_fallback_contract():
    ttt = TTTAdapter()

    def history_provider(req):
        return [{"a": "A", "b": "B", "winner": "A", "date": "2025-01-01"}]

    provider = build_rating_provider(ttt, history_provider)
    out = provider({"fighter_a": "A", "fighter_b": "B"})
    assert "a" in out and "b" in out
    assert "mu" in out["a"] and "sigma" in out["a"]
