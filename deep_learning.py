import numpy as np
import pandas as pd
import sys
from lin_reg import get_player_stats

import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense
from keras.callbacks import EarlyStopping

def convert2matrix(data_arr, lag):
    X, Y =[], []

    for i in range(len(data_arr)-lag):
        d=i+lag  
        X.append(data_arr[i:d])
        Y.append(data_arr[d])

    return np.array(X), np.array(Y)



def model_dnn(lag):

    model=Sequential()
    model.add(Dense(units=32, input_dim=lag, activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error',  optimizer='adam',metrics = ['mse', 'mae'])
    return model


seasons = ["2018-19"]#,"2019-20","2020-21"]
best = []

for i,season in enumerate(seasons):
    print("reading season ",season)
    
    p = get_player_stats(season)

    for id, player in p.items():
        average_points = np.mean(player["points"])
        player["average_points"] = average_points

    best += [player for id,player in p.items() if len(player["points"])>7]

best.sort(key=lambda player: player["average_points"])
best_player = best[-1]
best_player = pd.DataFrame(best_player)
best_player = best_player.drop(columns=["opponent","position","average_points"])
best_player["is_away"] = 1-best_player["is_home"][:]
#print(best_player)

n = 25
lag = 4

#data_train = best_player[:n]
#data_test = best_player[n:]
#
#train_mean = data_train.mean()
#train_std = data_train.std()
#test_mean = data_test.mean()
#test_std = data_test.std()
#
#train_df = (data_train - train_mean) / train_std
#test_df = (data_test - test_mean) / test_std


points_train = best_player["points"].values[:n]
points_train = (points_train - np.mean(points_train))/np.std(points_train)

points_test = best_player["points"].values[n:]
points_test = (points_test - np.mean(points_test))/np.std(points_test)

x_train, y_train = convert2matrix(points_train,lag)
x_test, y_test = convert2matrix(points_test,lag)


model=model_dnn(lag)
history=model.fit(x_train,y_train, epochs=200, batch_size=30, verbose=1, validation_data=(x_test,y_test),shuffle=False)#,callbacks=[EarlyStopping(monitor='val_loss', patience=10)])

train_score = model.evaluate(x_train, y_train, verbose=0)
print('Train Root Mean Squared Error(RMSE): %.2f; Train Mean Absolute Error(MAE) : %.2f ' 
% (np.sqrt(train_score[1]), train_score[2]))
test_score = model.evaluate(x_test, y_test, verbose=0)
print('Test Root Mean Squared Error(RMSE): %.2f; Test Mean Absolute Error(MAE) : %.2f ' 
% (np.sqrt(test_score[1]), test_score[2]))


plt.figure(figsize=(8,4))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Test Loss')
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epochs')
plt.legend(loc='upper right')
plt.show()



plt.figure(figsize=(8,4))
plt.plot(y_test[:lag], marker='.', label="actual")
plt.plot(test_score[:lag], 'r', label="prediction")
plt.tight_layout()
plt.subplots_adjust(left=0.07)
plt.ylabel('Ads Daily Spend', size=15)
plt.xlabel('Time step', size=15)
plt.legend(fontsize=15)
plt.show()