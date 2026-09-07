from amazon_reviews.pacer import HumanPacer, PROMOTE_TO_NORMAL_AFTER


def test_max_pace_caps_relaxed():
    events = []
    p = HumanPacer(force_mode="cautious", max_mode="normal", on_event=lambda e, d: events.append((e, d)))
    for _ in range(PROMOTE_TO_NORMAL_AFTER + 5):
        p.note_ok(got_new=True)
    assert p.mode == "normal"
    # Even with huge streak, cannot enter relaxed when max_mode=normal
    for _ in range(50):
        p.note_ok(got_new=True)
    assert p.mode == "normal"


def test_risk_resets_to_cautious():
    p = HumanPacer(force_mode="normal", max_mode="relaxed")
    p.note_risk("captcha")
    assert p.mode == "cautious"
    assert p.state.success_streak == 0
