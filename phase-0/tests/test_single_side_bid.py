from __future__ import annotations

from strategies.single_side_bid import SingleSideBidStrategy


def test_default_meteora_distribution_generated() -> None:
    strategy = SingleSideBidStrategy()

    assert strategy.build_distribution() == {
        -1: 10,
        -2: 15,
        -3: 20,
        -4: 30,
        -5: 40,
        -6: 55,
        -7: 75,
        -8: 100,
        -9: 140,
        -10: 200,
    }


def test_get_allocation_for_bin() -> None:
    strategy = SingleSideBidStrategy()

    assert strategy.get_allocation_for_bin(-4) == 30
    assert strategy.get_allocation_for_bin(1) == 0.0


def test_linear_and_exponential_modes() -> None:
    assert SingleSideBidStrategy(mode="linear", levels=3).build_distribution() == {
        -1: 10,
        -2: 20,
        -3: 30,
    }
    assert SingleSideBidStrategy(mode="exponential", levels=3).build_distribution() == {
        -1: 10,
        -2: 20,
        -3: 40,
    }
