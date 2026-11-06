
import pytest
from credit_card_rewards import reward_points, late_payment_fee, card_status


# Reward points tests
def test_classic_grocery():
    assert reward_points("classic", 1000, "grocery", False) == 10


def test_gold_dining_weekend():
    assert reward_points("gold", 1000, "dining", True) == 90


def test_platinum_travel_weekend():
    assert reward_points("platinum", 500, "travel", True) == 90


def test_classic_weekend():
    assert reward_points("classic", 500, "grocery", True) == 5


def test_fuel_purchase():
    assert reward_points("gold", 1000, "fuel", True) == 0


def test_unknown_card():
    with pytest.raises(ValueError, match="unknown card tier"):
        reward_points("diamond", 1000, "grocery", False)


def test_zero_amount():
    with pytest.raises(ValueError, match="invalid amount"):
        reward_points("gold", 0, "grocery", False)


# Late payment fee tests
def test_no_late_payment():
    assert late_payment_fee(5000, 0) == 0


def test_non_positive_outstanding():
    assert late_payment_fee(0, 10) == 0


def test_small_outstanding():
    assert late_payment_fee(500, 10) == 100


def test_medium_outstanding():
    assert late_payment_fee(5000, 10) == 500


def test_large_outstanding():
    assert late_payment_fee(15000, 10) == 1000


def test_late_more_than_30_days():
    assert late_payment_fee(5000, 45) == 1250


# Card status tests
def test_frozen_card():
    assert card_status(20, 0, True) == "frozen"


def test_blocked_card():
    assert card_status(20, 3, False) == "blocked"


def test_over_limit_risk():
    assert card_status(95, 0, False) == "over limit risk"


def test_watch_due_to_utilisation():
    assert card_status(50, 0, False) == "watch"


def test_watch_due_to_missed_payment():
    assert card_status(20, 1, False) == "watch"


def test_good_card():
    assert card_status(20, 0, False) == "good"