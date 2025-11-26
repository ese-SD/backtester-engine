from math import sqrt, exp, log


#----------------------------------------------------------------SPREAD MODELS--------------------------------------------------------


def model_spread_CS(context, upper_bound, close, correct_overnight=True, return_vol=False):
    """
    Estimate bid–ask spread using the Corwin–Schultz (2012) high–low spread estimator.

    Args:

    context (SlippageContext): Must contain in `context.extra["OCHLV"]` at least the last two days of OHLC data.
    upper_bound (float): Maximum allowed spread value (cap).
    close (float): Closing price of day t+1, used if applying the overnight correction.
    correct_overnight (bool, default=True): Adjusts for overnight price jumps between the previous close and next day's range.
    return_vol (bool, default=False): If True, also return the estimated volatility.

    Returns:
    spread (float):Estimated spread, capped between 0 and `upper_bound`.
    vol (float, optional): Estimated volatility (only if `return_vol=True`).

    Notes:
    Works best with liquid assets and daily data; may produce extreme values for illiquid assets.
    """

    # gets args from context
    H1=context.extra["OCHLV"][-2]["High"]
    H2=context.extra["OCHLV"][-1]["High"]
    L1=context.extra["OCHLV"][-2]["Low"]
    L2=context.extra["OCHLV"][-1]["Low"]

    #close: arg optionnel
    if correct_overnight:
        if(H2)<close:
            diff=close-H2
            H2+=diff
            L2-=diff
        elif (L2>close):
            diff=L2-close
            H2-=diff
            L2-=diff



    H=max(H1,H2)
    L=min(L1,L2)
    gamma=pow(log(H/L),2)
    beta=pow(log(H1/L1),2)+pow(log(H2/L2),2)
    alpha=(
        (sqrt(2*beta)-sqrt(beta))/(3-2*sqrt(2))
        -
        sqrt(gamma/(3-2*sqrt(2)))
    )
    spread=2*(exp(alpha)-1)/(1+exp(alpha))

    """Capping values to a realistic range to correct absurd values."""
    spread=min(max(spread,0),upper_bound)

    if return_vol:
        k1=4*log(2)
        k2=sqrt(8/pi)
        vol=(
            (sqrt(beta/2)-sqrt(beta)/k2)
        )+(
            sqrt(gamma/pow(k2,2)*(3-2*sqrt(2)))
        )
        return spread, vol
    else: return spread







#------------------------------------------------------------MARKET IMPACT MODELS--------------------------------------------------------


def model_market_impact_sqrt(context):
    """effective on low frequency strategies"""
    daily_volume=context.extra["OCHLV"][-1]["Volume"]
    volatility=0#?????
    return volatility* sqrt(context.order_size/daily_volume)


def market_impact_Almgren_Chriss(context):
    pass

#------------------------------------------------------------     QUEUE MODELS     --------------------------------------------------------

#------------------------------------------------------------AUCTION PRENIUM MODELS--------------------------------------------------------
