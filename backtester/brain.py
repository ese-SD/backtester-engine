import data_loaders
import strategies
from data_loaders.datafeed import Datafeed
from utils.market_forces import *
from datetime import datetime
from backtester.slippage_modeling import *
from backtester.signal import Signal
from collections import deque
import warnings


class Brain():
    
    """
    
    
    
    Args:

    slippage_context (SlippageContext): object that contains all the data that could be used to compute slippage, a sort of "snapshot" of Brain at the buy time
    execution_delay (datetime): how long orders are expected to take to be executed.
    
    
    
    """


    def __init__(self, slippage_context : SlippageContext, execution_delay : datetime):
        self.slippage_context=slippage_context 
        self.execution_delay=execution_delay 
        self.trade_history=list[Signal]
        self.signals_to_execute: deque[Signal] = deque() # signals to execute are in a queue

    def hook_data_feed(self, filepath):
        self.data_feed=Datafeed()
        self.data_feed.load_data(self,filepath)
    
    def hook_strategy(self, strategy_name):
        self.strategy=strategies.strategy_name#load_strategy?

    def init_meta_args(self, spread_fct, spread_coeff, model_impact_fct, model_impact_coeff, fee_structure):
        self.spread_fct=spread_fct
        self.spread_coeff=spread_coeff
        self.model_impact_fct=model_impact_fct
        self.model_impact_coeff=model_impact_coeff
        self.fee_structure=fee_structure


    def hook_wallet(self, wallet):
        self.wallet=wallet

    def hook_slippage_model(self, model : SlippageModel):
        self.slippage_model=model


    def execute_signals(self, current_price, current_time):
        if current_time==self.data_feed.data.index[-1]:
            print("Can't execute signals on the last bar, because execution delay requires the signal to be executed on the next bar.")
            return 0
        signal= self.signals_to_execute.popleft()
        invalid_orders=deque()
        signals_to_repeat=deque()
        while signal is not None:
            
        #for signal in self.signals_to_execute:
            if signal.ticker!=self.data_feed.ticker:
                print(f"Signal {signal} received on {current_time} is invalid because ticker {signal.ticker} doesn't match the datafeed's ticker.")
                continue
            match signal.ttype:
                case "BUY_MARKET":
                    fill_price=self.slippage_model.compute_fill_price(self.slippage_context)
                    fee=self.fee_structure.compute_fee(signal.size, fill_price)
                    if self.fee_structure.application == "on top":                
                        if self.wallet.cash<fee+signal.size*fill_price:                  #TODO: comment factoriser ces 3 lignes ?
                            warnings.warn("Order {signal} cannot be executed: insufficient funds.")
                            invalid_orders.append(signal)
                            continue
                        self.wallet.cash-=(fee+signal.size*fill_price)
                        self.wallet.stocks[signal.ticker]+=signal.size
                        self.trade_history.append(signal)
                    else:
                        if self.wallet.cash>signal.size*fill_price: 
                            warnings.warn("Order {signal} cannot be executed: insufficient funds.")
                            invalid_orders.append(signal)
                            continue
                        actual_share_nb=signal.size-fill_price/fee
                        self.wallet.cash-=signal.size*fill_price
                        self.wallet.stocks[signal.ticker]+=actual_share_nb
                        self.trade_history.append(signal)

                case "SELL_MARKET":
                    fill_price=self.slippage_model.compute_fill_price(self.slippage_context)
                    fee=self.fee_structure.compute_fee(signal.size, fill_price)
                    if self.fee_structure.application == "on top":
                        if self.wallet.cash<fee or self.wallet.shares[signal.ticker]<signal.size:
                            warnings.warn("Order {signal} cannot be executed: insufficient funds.")
                            invalid_orders.append(signal)
                            continue
                        self.wallet.cash-=(fee+signal.sizer*fill_price)
                        self.wallet.stocks[signal.ticker]-=signal.size
                        self.trade_history.append(signal)
                    else:
                        if signal.size*fill_price<fee or self.wallet.share[signal.ticker]<signal.size: 
                            warnings.warn("Order {signal} cannot be executed: sell is to small to cover fees.")
                            invalid_orders.append(signal)
                            continue
                        self.wallet.cash+=(signal.size*fill_price-fee)
                        self.wallet.stocks[signal.ticker]-=signal.size
                        self.trade_history.append(signal)

                case "BUY_LIMIT": #pas encore implemté
                    """
                    if is_limit_valid(signal):
                        executer le signal
                    else:
                        signals_to_repeat.append(signal)
                    """
                    pass
                case "SELL_LIMIT": #pas encore implemté
                    """
                    if is_limit_valid(signal):
                        executer le signal
                    else:
                        signals_to_repeat.append(signal)
                    """
                    pass
                case "CANCEL_LIMIT_ORDER":
                    """
                    chercher dans la queue des signaux a executer et de ceux a repeter, si on trouve le signal avec l'id specifié, le retirer.
                    peut eventuellement utiliser order.size comme l'id de l'order a supp, pratique mais + glr a comprendre.
                    """
                    pass

            signal= self.signals_to_execute.popleft()
        
        
        
        # All remaining signals are invalid and have to be deleted
        # ou renvoyer feedback des signaux invalide?
        #pour les LIMIT, faut les laisser dans la queue tant qu'ils sont pas executés, expirés, ou annulés (grace a l'id)

        self.signals_to_execute.append(signals_to_repeat)
        return invalid_orders


    def update_context(self):
        pass


    def run(self,):
        #si la frequence de la strategy est incompatible avec le data feed, erreur
        #if self.strategy.frequency!=data_feed
        """
        iterer sur le datafeed, et a chaque iteration, appeler next de strategy"""
        for i in Datafeed.data:
            self.update_context()#dans le contexte, la date d'execution (ie la date sur laquelle est appliquée le reste du slippage genre spread, auction prenium etc
            #doit etre avancée de 1 pour simuler le delai)
            new_signals=self.strategy.next(i)
            self.signals_to_execute.append(new_signals)
            self.execute_signals()

    
    



if __name__ == "__main__":
    pass