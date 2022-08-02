import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt

def calculate_expected_score_average_model(players,home_teams,away_teams,n_norm_week,future_week):
              
    lin_model = ri.read_linear_scoring_model("average_simple_linear_model.txt")
    diff = []
    for p in players:
    
        if p.position == "gkp":
            pos = 1
        elif p.position == "def":
            pos = 2
        elif p.position == "mid":
            pos = 3
        elif p.position == "fwd":
            pos = 4       
        else:
            print("Unknown position",p.position)

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue
            
        mod = lin_model[pos]

        if len(p.score) == 0:
            prev_points = p.points_last_round
            average_points = p.tot_points/n_norm_week
        else:
            prev_points = p.score[-1]
            average_points = (p.tot_points+sum(p.score))/(n_norm_week+future_week)

        score = 0.0
        for i in range(n_home):
            is_home = 1
            is_away = 0
            
            vals = [prev_points,average_points,p.minutes/n_norm_week,is_home,is_away,p.assists/n_norm_week,p.goals_conceded/n_norm_week,p.clean_sheets/n_norm_week,p.goals_scored/n_norm_week]
            score += mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))     
            
        for i in range(n_away):
            is_home = 0
            is_away = 1
            
            vals = [prev_points,average_points,p.minutes/n_norm_week,is_home,is_away,p.assists/n_norm_week,p.goals_conceded/n_norm_week,p.clean_sheets/n_norm_week,p.goals_scored/n_norm_week]
            score += mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))     

        p.score.append(score)

def calculate_expected_score_big_model(players,home_teams,away_teams,prev_game_week,future_week):
              
    lin_model = ri.read_linear_scoring_model("big_simple_linear_model.txt")
    diff = []
    for p in players:
    
        if p.position == "gkp":
            pos = 1
        elif p.position == "def":
            pos = 2
        elif p.position == "mid":
            pos = 3
        elif p.position == "fwd":
            pos = 4       
        else:
            print("Unknown position",p.position)
        
        #if pos != 2:
        #    continue

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue
            
        mod = lin_model[pos]

        h = p.history
            
        average_points = (sum(h["total_points"])+sum(p.score))/(prev_game_week+future_week)
        
        average_min = sum(h["minutes"])/prev_game_week
        average_assist = sum(h["assists"])/prev_game_week
        average_goals_conceded = sum(h["goals_conceded"])/prev_game_week
        average_clean_sheets = sum(h["clean_sheets"])/prev_game_week
        average_goals_scored = sum(h["goals_scored"])/prev_game_week

        if len(p.score) == 0:
            prev_points = h["total_points"][-1]
            prev_min = h["minutes"][-1]
            prev_assist = h["assists"][-1]
            prev_goals_conceded = h["goals_conceded"][-1]
            prev_clean_sheets = h["clean_sheets"][-1]
            prev_goals_scored = h["goals_scored"][-1]
        
        else:
            prev_points = p.score[-1]        
            prev_min = average_min
            prev_assist = average_assist
            prev_goals_conceded = average_goals_conceded
            prev_clean_sheets = average_clean_sheets
            prev_goals_scored = average_goals_scored

        score = 0.0
        for i in range(n_home):
            is_home = 1
            is_away = 0

            vals = [prev_points,average_points,prev_min,average_min,is_home,is_away,prev_assist,average_assist,prev_goals_conceded,average_goals_conceded,prev_clean_sheets,average_clean_sheets,prev_goals_scored,average_goals_scored]
            score += mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))     
            
        for i in range(n_away):
            is_home = 0
            is_away = 1

            vals = [prev_points,average_points,prev_min,average_min,is_home,is_away,prev_assist,average_assist,prev_goals_conceded,average_goals_conceded,prev_clean_sheets,average_clean_sheets,prev_goals_scored,average_goals_scored]
            score += mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))     

        p.score.append(score)

def calculate_expected_score_points_model(players,home_teams,away_teams):
              
    lin_model = ri.read_linear_scoring_model("simple_points_model.txt")
    diff = []
    for p in players:
    
        if p.position == "gkp":
            pos = 1
        elif p.position == "def":
            pos = 2
        elif p.position == "mid":
            pos = 3
        elif p.position == "fwd":
            pos = 4       
        else:
            print("Unknown position",p.position)
        

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue
            
        mod = lin_model[pos]

        prev_points = list(p.history["total_points"])+list(p.score)        
        n = len(prev_points)

        average = np.mean(prev_points)

        if n < 4:
            prev_points = [0]*(4-n)+prev_points
        else:
            prev_points = prev_points[n-4:]

        coeffs = prev_points+[average]

        score = 0.0
        for i in range(n_home):

            score += sum(v*c for v,c in zip(coeffs,mod))     
            
        for i in range(n_away):

            score += sum(v*c for v,c in zip(coeffs,mod))     

        p.score.append(score)

def calculate_expected_score_from_form(players,home_teams,away_teams):
              
    for p in players:       

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue            

        prev_points = list(p.history["total_points"])+list(p.score)        
        
        #print(np.mean(prev_points[-4:]),np.median(prev_points[-4:]))

        prev = prev_points[-5:]
        i_min = np.argmin(prev)
        i_max = np.argmax(prev)
        prev = [val for i,val in enumerate(prev) if i != i_min and i != i_max]

        average = np.median(prev)

        score = average * (n_home+0.9*n_away)
        #score = np.median(prev_points[-4:]) * (n_home+0.9*n_away)
        #print(score,np.median(prev_points[-6:]) * (n_home+0.9*n_away))
        p.score.append(score)

            
def calculate_smart_score(players,home_teams,away_teams):

    from sklearn.linear_model import LinearRegression
    from skforecast.ForecasterAutoreg import ForecasterAutoreg
    import pandas as pd

    forecaster = ForecasterAutoreg(regressor = LinearRegression(), lags = 4)

    for p in players:

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        n_matches = n_home+n_away

        if n_matches == 0:        
            p.score.append(0.0)
            continue

        try:
            prev_points = list(p.history["total_points"])+list(p.score)
            minutes_played = list(p.history["minutes"])
        except AttributeError:
            print(f"No history found for {p.display()}")
            p.score.append(0.0)
            continue
        
        minute_factor = 1.0
        if np.mean(minutes_played[-2:]) < 60.0:
            minute_factor = 0.5

        if len(prev_points) <= 4:
            p.score.append(np.mean(prev_points)*n_matches*minute_factor)
            continue
        
        average = np.mean(prev_points[-4:])

        forecaster.fit(y=pd.Series(prev_points))
        try:
            prediction = forecaster.predict(steps=1).values[0]
        except IndexError:
            print(f"Unable to fit data for {p.display()}")
            prediction = average

        sc = min(average,prediction)
        if sc < 0.0:
            sc = 0.0

        #if prediction < -2 or prediction > 10:
        #    print(p.name,average,prediction,prev_points)

        #if sc < 0.0:
        #    sc = max(average,prediction)

        p.score.append(sc*n_matches*minute_factor)


game_week = 16

url_base = "https://fantasy.eliteserien.no/api/"     

url_team = f"{url_base}entry/9438/event/{game_week-1}/picks/"

players,teams = ri.scrape_players(url_base)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

filename_history = f"eliteserien\\2022\\player_history_el_{game_week-1}.txt"

try:
    ri.read_player_history(filename_history,players)
except FileNotFoundError:
    ri.create_player_history(url_base,filename_history,game_week-1,wait_time=0.6)
    ri.read_player_history(filename_history,players)

not_playing = {}
#not_playing["Odd"] = ["Jonassen"]
#not_playing["Bodø/Glimt"] = ["Pellegrino"]
#not_playing["Rosenborg"] = ["Sæter"]
#not_playing["FK Haugesund"] = ["Søderlund"]
#not_playing["Vålerenga"] = ["Dønnum","Borchgrevink"]
#not_playing["Mjøndalen"] = ["Thomas"]
#not_playing["Viking FK"] = ["Berisha"]
#not_playing["Stabæk"] = []
not_playing["Sarpsborg 08"] = ["Maigaard"]
#not_playing["Molde"] = ["Wolff Eikrem"]
#not_playing["Tromsø"] = ["Totland"]
#not_playing["Lillestrøm"] = ["Helland"]
#not_playing["Kristiansund BK"] = ["Strand Nilsen"]
#not_playing["Strømsgodset"] = ["Valsvik"]
#not_playing["Sandefjord"] = ["Ofkir"]
#not_playing["Hamkam"] = ["Kurucay"]



horizon = 2
for i in range(horizon):

    home_teams,away_teams,difficulty = ri.scrape_fixtures(url_base,teams,game_week+i)

    #calculate_expected_score_average_model(players,home_teams,away_teams,game_week-1,i)
    #calculate_expected_score_big_model(players,home_teams,away_teams,game_week-1,i)
    #calculate_expected_score_points_model(players,home_teams,away_teams)
    calculate_expected_score_from_form(players,home_teams,away_teams)
    #calculate_smart_score(players,home_teams,away_teams)

    if i == 0:
        for team, out in not_playing.items():

            for p in players:
                if p.team != team:
                    continue
                if p.name in out:
                    p.score[i] *= 0.0

team_worth = bank #-1.3
print("Existing players:")
for p in existing_players:
    p.display()
    print("\t",p.history["total_points"])
    team_worth += p.cost

#sc = [p.score[0] for p in players]
#plt.plot(sc,"ro")
#plt.show()
#sys.exit()    


wild_card = False
rik_onkel = False
spiss_rush = False


n_max_transf = 1
#n_free_transf = 1

if rik_onkel:    
    team_worth = 10000
    n_free_transf = 15
    n_max_transf = 15
    
if wild_card:    
    n_free_transf = 15
    n_max_transf = 15
        
if spiss_rush:
    for p in players:
        if p.position=="fwd":
            p.score[0] *= 2

print("")
print("Bank:",bank)
print("Total value:",team_worth)
print("Free transfers:",n_free_transf)
print("")    

#solver_path = r"C:\Users\Christian\CPLEX 20_10\cplex.exe"
solver_path = r"C:\My Stuff\CPLEX 20\cplex.exe"

opt = pr.MultiWeekFantasyOptimizer(solver_path)
opt.build_best_formation_model(players,horizon,team_worth,existing_players,n_free_transf,n_max_transf=n_max_transf)


#opt.required_players([p for p in existing_players if "Berisha" in p.name])

opt.solve_model()
opt.display_results()
