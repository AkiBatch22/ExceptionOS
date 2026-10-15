from backend.app.services.recommendations import recommend_actions


def test_recommendations_cover_only_basic_allowlisted_issues(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_RECOMMENDATIONS", "false")

    actions = recommend_actions(
        [
            {"reason": "unknown_sku", "sku": "X-1"},
            {"reason": "possible_fraud", "customer": "Acme Inc."},
        ]
    )

    assert actions == [
        "Confirm the supplier SKU and map it to an internal SKU."
    ]


def test_no_recommendation_is_generated_for_non_basic_issue(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_RECOMMENDATIONS", "false")

    assert recommend_actions([{"reason": "possible_fraud"}]) == []
