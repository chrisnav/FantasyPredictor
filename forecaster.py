from ast import Index
import numpy as np
import pandas as pd
import sys

import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
plt.rcParams['lines.linewidth'] = 1.5

from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.ForecasterAutoregCustom import ForecasterAutoregCustom
from skforecast.ForecasterAutoregMultiOutput import ForecasterAutoregMultiOutput
from skforecast.model_selection import grid_search_forecaster
from skforecast.model_selection import backtesting_forecaster

from joblib import dump, load

# Warnings configuration
# ==============================================================================
import warnings
warnings.filterwarnings('ignore')

from lin_reg import get_player_stats
import time

def grid_search_fit(data:pd.DataFrame, n:int) -> ForecasterAutoreg:

    data_train = data[:n]

    exog_train = pd.DataFrame()
    exog_train["is_home"] = data_train["is_home"]
    exog_train["is_away"] = data_train["is_away"]

    steps = len(data)-n

    forecaster = ForecasterAutoreg(
                    regressor = RandomForestRegressor(random_state=123,n_jobs=12),
                    lags      = 6
                )
    lags_grid = [1,2,3,4,5,6,7,8]

    # Regressor's hyperparameters
    param_grid = {'n_estimators': [10, 25, 50, 100, 200],
                'max_depth': [1, 3, 5, 10, 20]}

    results_grid = grid_search_forecaster(
                            forecaster         = forecaster,
                            y                  = data_train["points"],
                            exog               = exog_train,
                            param_grid         = param_grid,
                            lags_grid          = lags_grid,
                            steps              = steps,
                            refit              = True,
                            metric             = 'mean_squared_error',
                            initial_train_size = int(len(data_train["points"])*0.75),
                            return_best        = True,
                            verbose            = False
                )
    print(results_grid)    

    return forecaster


seasons = ["2018-19","2019-20","2020-21"]
best = []
for i,season in enumerate(seasons):
    print("reading season ",season)
    
    p = get_player_stats(season)

    for id, player in p.items():
        average_points = np.mean(player["points"])
        player["average_points"] = average_points

    best += [player for id,player in p.items() if len(player["points"])>7]

best.sort(key=lambda player: player["average_points"])


#reg = RandomForestRegressor(max_depth=20, n_estimators=10, random_state=123, n_jobs=12)
forecaster = ForecasterAutoreg(regressor = LinearRegression(), lags = 4)

#forecaster2 = ForecasterAutoreg(regressor = LinearRegression(),lags =4)
#forecaster2 = ForecasterAutoreg(regressor = Lasso(alpha=0.005,random_state=123),lags = 4)

n_win = 0
n_lose = 0
n_equal = 0
sum1 = 0.0
sum2 = 0.0
for player in best:
    #print(player["position"])

    data = pd.DataFrame(player)
    data["is_away"] = 1 - data["is_home"]

    steps = 3
    n = len(data) - steps

    data_train = data[:n]
    data_test = data[n:]

    average = np.mean(data_train["points"][-4:])


    exog_train = pd.DataFrame()
    exog_train["is_home"] = data_train["is_home"]
    exog_train["is_away"] = data_train["is_away"]

    exog_test = pd.DataFrame()
    exog_test["is_home"] = data_test["is_home"]
    exog_test["is_away"] = data_test["is_away"]

    #forecaster = grid_search_fit(data,n)

    forecaster.fit(y=data_train["points"])
    #forecaster2.fit(y=data_train["points"])
    try:
        predictions = forecaster.predict(steps=steps)
        #predictions2 = forecaster2.predict(steps=steps)
    except IndexError:
        print("oops",len(data))
        continue
    
    predictions3 = [min(average,p) for p in predictions]

    error_mse = mean_squared_error(y_true = data_test["points"],y_pred = predictions)
    #error_mse2 = mean_squared_error(y_true = data_test["points"],y_pred = predictions2)
    error_mse3 = mean_squared_error(y_true = data_test["points"],y_pred = predictions3)

    sum1 += error_mse
    sum2 += error_mse3
    #print(f"Test error (mse): {error_mse} {error_mse3}")
    #plt.plot(range(n),data_train["points"],"k")
    #plt.scatter(range(n,n+steps),data_test["points"],color="r")
    #plt.scatter(range(n,n+steps),predictions,color="b")
    #plt.scatter(range(n,n+steps),predictions3,color="m")
    #plt.show()

    #if average > 3 and np.amin(data_train["points"][-4:]) > 0.0:
        
    if abs(error_mse-error_mse3) < 0.000001:
        n_equal += 1
        continue
    
    if error_mse < error_mse3:
        n_win += 1
    else:
        n_lose += 1

n_tot = n_win+n_lose+n_equal
print(n_win,n_lose,n_equal,n_tot)
print(sum1/n_tot,sum2/n_tot)