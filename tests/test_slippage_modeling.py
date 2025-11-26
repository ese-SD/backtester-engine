import pytest
from functools import partial
from math import isclose

import backtester.slippage_modeling as sm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_context():
    """A simple concrete SlippageContext-like object for testing SlippageModel."""
    class SimpleContext:
        def __init__(self, price):
            self.price = price
            self.extra = {}
            self.order_size = 0
            self.timestamp = None
    return SimpleContext


@pytest.fixture
def dummy_context(simple_context):
    """Instance of the simple context with default price=100."""
    return simple_context(100.0)


@pytest.fixture
def mock_context_class():
    """A minimal concrete subclass of SlippageContext to test abstract behavior."""
    class ConcreteContext(sm.SlippageContext):
        def update_context(self, new_data):
            self.extra.update(new_data)
    return ConcreteContext


# ---------------------------------------------------------------------------
# 1. PARTIAL FUNCTION CONSTRUCTION
# ---------------------------------------------------------------------------

def test_partial_functions_are_created(dummy_context):
    """Ensure SlippageModel builds partial functions correctly with provided params."""

    # Simple mock functions
    def spread_fct(context, x, y): return x + y
    params = {"spread": {"x": 1, "y": 2}, "mi": {}, "queue": {}, "ap": {}}

    model = sm.SlippageModel(
        spread_fct=spread_fct, spread_coeff=1.0,
        market_impact_fct=None, MI_coeff=0.0,
        queue_fct=None, queue_coeff=0.0,
        auct_prenium_fct=None, AP_coeff=0.0,
        params=params
    )

    fct, coeff = model.spread

    assert isinstance(fct, partial)
    assert coeff == 1.0

    result = fct(dummy_context)
    assert result == 3  # 1 + 2


def test_none_functions_are_stored_correctly():
    """If user passes None, SlippageModel must store (None, coeff) without crashing."""
    params = {"spread": {}, "mi": {}, "queue": {}, "ap": {}}
    model = sm.SlippageModel(
        spread_fct=None, spread_coeff=1.0,
        market_impact_fct=None, MI_coeff=2.0,
        queue_fct=None, queue_coeff=3.0,
        auct_prenium_fct=None, AP_coeff=4.0,
        params=params
    )

    assert model.spread[0] is None
    assert model.market_impact[0] is None
    assert model.queue[0] is None
    assert model.auction_premium[0] is None


# ---------------------------------------------------------------------------
# 2. COMPUTE_FILL_PRICE BEHAVIOR
# ---------------------------------------------------------------------------

def test_compute_fill_price_all_components(dummy_context):
    """Ensures compute_fill_price applies each component with their coefficients."""

    def f1(context): return 1
    def f2(context): return 2
    def f3(context): return 3
    def f4(context): return 4

    params = {"spread": {}, "mi": {}, "queue": {}, "ap": {}}

    model = sm.SlippageModel(
        spread_fct=f1, spread_coeff=0.1,
        market_impact_fct=f2, MI_coeff=0.2,
        queue_fct=f3, queue_coeff=0.3,
        auct_prenium_fct=f4, AP_coeff=0.4,
        params=params,
    )

    expected = (
        dummy_context.price
        + 0.1 * 1
        + 0.2 * 2
        + 0.3 * 3
        + 0.4 * 4
    )
    result = model.compute_fill_price(dummy_context)

    assert isclose(result, expected)


def test_compute_fill_price_single_component(dummy_context):
    """Check SlippageModel with only one active component does not call Nones incorrectly."""

    def f1(context): return 5

    params = {"spread": {}, "mi": {}, "queue": {}, "ap": {}}

    model = sm.SlippageModel(
        spread_fct=f1, spread_coeff=2.0,
        market_impact_fct=None, MI_coeff=0.0,
        queue_fct=None, queue_coeff=0.0,
        auct_prenium_fct=None, AP_coeff=0.0,
        params=params
    )

    expected = dummy_context.price + 2.0 * 5
    result = model.compute_fill_price(dummy_context)
    assert isclose(result, expected)


def test_compute_fill_price_type_stability(simple_context):
    """Ensure compute_fill_price always returns a float even if price is int."""

    int_context = simple_context(price=10)

    def f1(context): return 1

    params = {"spread": {}, "mi": {}, "queue": {}, "ap": {}}

    model = sm.SlippageModel(
        spread_fct=f1, spread_coeff=0.5,
        market_impact_fct=None, MI_coeff=0.0,
        queue_fct=None, queue_coeff=0.0,
        auct_prenium_fct=None, AP_coeff=0.0,
        params=params
    )

    result = model.compute_fill_price(int_context)
    assert isinstance(result, float)
    assert isclose(result, 10 + 0.5 * 1.0)


# ---------------------------------------------------------------------------
# 5. ABSTRACT CLASS BEHAVIOR (SlippageContext)
# ---------------------------------------------------------------------------

def test_slippage_context_is_abstract():
    """SlippageContext must not be instantiable."""
    with pytest.raises(TypeError):
        sm.SlippageContext(price=1, order_size=1, timestamp=None)


def test_slippage_context_subclass_must_implement_update(mock_context_class):
    """Valid concrete subclass must be instantiable and update_context must work."""

    ctx = mock_context_class(price=100, order_size=10, timestamp=None)
    assert isinstance(ctx, sm.SlippageContext)

    ctx.update_context({"a": 1})
    assert ctx.extra["a"] == 1
