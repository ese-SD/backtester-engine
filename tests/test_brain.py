import numpy as np
import datetime
import random as rd
import pandas as pd


# ---------------------------------------------------------
# helper functions
# ---------------------------------------------------------




#create mock dataframe
open=[]
high=[]
low=[]
close=[]
vol=[]
dates=[]
start_date=datetime.datetime(2020, 1, 1, 10, 0,0)

for i in range (20):
    dates.append(datetime.datetime(2020, 1, i))
    open.append(1000+10*rd.randomd())
    high.append(1000+10*rd.randomd())
    low.append(1000+10*rd.randomd())
    close.append(1000+10*rd.randomd())
    vol.append(10000+1000*rd.randomd())

data={
    "Open":open,
    "High":high,
    "Low":low,
    "Close":close,
    "Volume":vol
}

df=pd.DataFrame(data,index=dates)
print(df)

