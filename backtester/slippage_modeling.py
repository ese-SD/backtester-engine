from dataclasses import dataclass, field
from typing import Any
from math import log,sqrt,exp,pi
from functools import partial, partialmethod
from datetime import datetime
from abc import ABC, abstractmethod



@dataclass
class SlippageContext(ABC):
    """
    Snapshot of the information used to compute slippage at a given moment.
    Common fields (price, order_size, timestamp) are always required.
    Model-specific or temporary fields go into `extra`.
    Each concrete slippage model must implement `update_context() to refresh the context using the latest data from Brain.
    """
    price: float
    order_size: int
    timestamp: datetime
    # Optional additional informations required by specific slippage components. ex previous OHLC bars
    extra: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def update_context(self):
        """
        Updates the context with new inputs coming from Brain.

        This allows different slippage models to request or maintain different types of state like rolling OHLC windows, intraday data etc
        """
        pass



class SlippageModel:
    """
    Models slippage when filling an order based on the order and current market conditions.

    User can customize and create their own slippage model by chosing different component function and their parameters.
    """

    def __init__(self, spread_fct=None, spread_coeff=0.0,
                 market_impact_fct=None, MI_coeff=0.0,
                 queue_fct=None, queue_coeff=0.0,
                 auct_prenium_fct=None, AP_coeff=0.0,
                 params=None):
        
        """
        Initialize a SlippageModel with optional components.

        Args:
            spread_fct (callable, optional): Function to model the spread component.
            spread_coeff (float, optional): Coefficient to scale the spread contribution. Defaults to 0.0.
            market_impact_fct (callable, optional): Function to model the market impact component.
            MI_coeff (float, optional): Coefficient to scale the market impact contribution. Defaults to 0.0.
            queue_fct (callable, optional): Function to model queue effects.
            queue_coeff (float, optional): Coefficient to scale the queue effect contribution. Defaults to 0.0.
            auct_prenium_fct (callable, optional): Function to model auction premium.
            AP_coeff (float, optional): Coefficient to scale the auction premium contribution. Defaults to 0.0.
            params (dict, optional): Dictionary of parameter dictionaries for each component.
                Example:
                    {
                        "spread": {"window": 10},
                        "mi": {"factor": 0.02}
                    }
        """
        
        params = params or {}

        partial_spread = partial(spread_fct, **params.get("spread", {})) if spread_fct else None
        partial_mi= partial(market_impact_fct, **params.get("mi", {})) if market_impact_fct else None
        partial_queue = partial(queue_fct, **params.get("queue", {})) if queue_fct else None
        partial_ap = partial(auct_prenium_fct, **params.get("ap", {})) if auct_prenium_fct else None
        self.spread = (partial_spread, spread_coeff)
        self.market_impact = (partial_mi, MI_coeff)
        self.queue = (partial_queue, queue_coeff)
        self.auction_premium = (partial_ap, AP_coeff)

    def compute_fill_price(self, context):
        """
        Compute the adjusted fill price given a trading context.

        Args:
            context (SlippageContext): Snapshot of trading conditions when filling the order.

        Returns:
            total (float): The adjusted fill price after applying all slippage components.
        """
        self.context=context
        total=float(context.price)
        for fct, coeff in [self.spread, self.market_impact, self.queue, self.auction_premium]:
            if fct is not None:
                total += coeff * fct(context)
        return total
    

