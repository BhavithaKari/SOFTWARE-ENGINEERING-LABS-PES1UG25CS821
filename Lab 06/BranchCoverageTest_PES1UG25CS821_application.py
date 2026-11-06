
import pytest
from credit_card_rewards import reward_points, late_payment_fee, card_status


# Reward points: card tier and amount validation
def test_invalid_card_tier():
    with pytest.raises(ValueError, match="unknown card tier"):
        reward_points("diamond", 1000, "grocery", False)


def test_invalid_amount():
    with pytest.raises(ValueError, match="invalid amount"):
        reward_points("gold", -100, "grocery", False)


# Reward points: fuel and category branches
def test_fuel_category():
    assert reward_points("gold", 1000, "fuel", False) == 0


def test_dining_category():
    assert reward_points("gold", 1000, "dining", False) == 40


def test_travel_category():
    assert reward_points("platinum", 500, "travel", False) == 40


def test_grocery_category():
    assert reward_points("classic", 1000, "grocery", False) == 10


# Reward points: weekend and card tier branches
def test_weekday_purchase():
    assert reward_points("gold", 1000, "grocery", False) == 20


def test_classic_weekend():
    assert reward_points("classic", 1000, "grocery", True) == 10


def test_gold_weekend():
    assert reward_points("gold", 1000, "grocery", True) == 70


# Late payment fee: initial validation branches
def test_zero_days_late():
    assert late_payment_fee(5000, 0) == 0


def test_negative_days_late():
    assert late_payment_fee(5000, -5) == 0


def test_zero_outstanding():
    assert late_payment_fee(0, 10) == 0


def test_negative_outstanding():
    assert late_payment_fee(-500, 10) == 0


# Late payment fee: outstanding amount branches
def test_outstanding_below_1000():
    assert late_payment_fee(500, 10) == 100


def test_outstanding_exactly_1000():
    assert late_payment_fee(1000, 10) == 100


def test_outstanding_between_1000_and_10000():
    assert late_payment_fee(5000, 10) == 500


def test_outstanding_exactly_10000():
    assert late_payment_fee(10000, 10) == 500


def test_outstanding_above_10000():
    assert late_payment_fee(15000, 10) == 1000


# Late payment fee: delay duration branches
def test_exactly_30_days_late():
    assert late_payment_fee(5000, 30) == 500


def test_more_than_30_days_late():
    assert late_payment_fee(5000, 31) == 1250


# Card status: frozen and blocked branches
def test_frozen_card():
    assert card_status(50, 0, True) == "frozen"


def test_not_frozen_card():
    assert card_status(20, 0, False) == "good"


def test_three_missed_payments():
    assert card_status(20, 3, False) == "blocked"


def test_more_than_three_missed_payments():
    assert card_status(20, 4, False) == "blocked"


# Card status: utilisation branches
def test_utilisation_above_90():
    assert card_status(95, 0, False) == "over limit risk"


def test_utilisation_exactly_90():
    assert card_status(90, 0, False) == "watch"


def test_utilisation_above_30():
    assert card_status(50, 0, False) == "watch"


# Card status: missed payment and good status branches
def test_missed_payment_with_low_utilisation():
    assert card_status(20, 1, False) == "watch"


def test_low_utilisation_no_missed_payments():
    assert card_status(20, 0, False) == "good"