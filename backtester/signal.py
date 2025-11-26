class Signal():
    """
    This class contains the informations necessary to place and then fulfill an order.

    It allows a Strategy to place various typs of orders, which will get picked up by Brain to be verified and then fulfilled.
    
    Attributes:
        id (int): id of the signal/order.
        ttype (str): type of signal.
        ticker (str): the ticker on which the order is placed.
        size (float): the number of shares intended to be bought.
        price (float): the price at which the shares should be bought.
        
    """
    def __init__(self, id, ttype, ticker, size, price):
        """
        Args:
        id (int): used by Brain for the historic, and to delete limit orders, among other things.
        ttype (str): the type of the order, on which depends how it will be handled by Brain.
        ticker (str): the ticker on which the order is placed.
        size (float): the number of share to buy (or *want* to buy, in case of market orders, because of slippage)
        price (float): share price at the time of the signal. For limits, it sets the exact price at which to fulfill the order.
        
        """
        types=["BUY_MARKET", "BUY_LIMIT", "SELL_MARKET", "SELL_LIMIT"]
        num=(int,float)
        if ( isinstance(id, int) and 
            ttype in types and 
            isinstance(ticker, str) and 
            isinstance(size, num) and 
            isinstance(price, num) 
):
            self.id=id
            self.type=type
            self.ticker=ticker
            self.size=size
            self.price=price
        else:
            raise ValueError("Invalid arguments.")