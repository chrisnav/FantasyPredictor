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

def calculate_expected_score_points_model(players,home_teams,away_teams,prev_game_week,future_week):
              
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
          
        average_points = (p.tot_points + sum(p.score))/(prev_game_week+future_week)
        if len(p.score) == 0:
            prev_points = p.history["total_points"][-1]
            try:
                prev_points_2 = p.history["total_points"][-2]
            except IndexError:
                prev_points_2 = 0
            
        elif len(p.score) == 1:
            prev_points = p.score[-1]
            prev_points_2 = p.history["total_points"][-1]
        else:
            prev_points = p.score[-1]
            prev_points_2 = p.score[-2]
        
        score = 0.0
        for i in range(n_home):

            vals = [prev_points,prev_points_2,average_points,prev_points**2,prev_points_2**2,average_points**2]
            score += sum(v*c for v,c in zip(vals,mod))     
            
        for i in range(n_away):

            vals = [prev_points,prev_points_2,average_points,prev_points**2,prev_points_2**2,average_points**2]
            score += sum(v*c for v,c in zip(vals,mod))     

        p.score.append(score)

            
game_week = 22

url_base = "https://fantasy.eliteserien.no/api/"     

url_team = f"{url_base}entry/29209/event/{game_week-1}/picks/"

players,teams = ri.scrape_players(url_base)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

filename_history = f"eliteserien\\2021\\player_history_el_{game_week-1}.txt"

try:
    ri.read_player_history(filename_history,players)
except FileNotFoundError:
    ri.create_player_history(url_base,filename_history,game_week-1)
    ri.read_player_history(filename_history,players)

not_playing = {}
not_playing["Odd"] = ["Bakenga"]
not_playing["Bodø/Glimt"] = ["Sørli","Saltnes"]
not_playing["Rosenborg"] = ["Andersson"]
not_playing["FK Haugesund"] = ["Desler"]
not_playing["Vålerenga"] = ["Dønnum","Borchgrevink"]
not_playing["Mjøndalen"] = ["Thomas"]
not_playing["Viking FK"] = ["Haugen"]
not_playing["Stabæk"] = []
not_playing["Sarpsborg 08"] = []
not_playing["Tromsø"] = []

horizon = 4
for i in range(horizon):

    home_teams,away_teams,difficulty = ri.scrape_fixtures(url_base,teams,game_week+i)

    #calculate_expected_score_average_model(players,home_teams,away_teams,game_week-1,i)
    #calculate_expected_score_big_model(players,home_teams,away_teams,game_week-1,i)
    calculate_expected_score_points_model(players,home_teams,away_teams,game_week-1,i)
    
#    if i == 0:
    for team, out in not_playing.items():
        
        for p in players:
            if p.team != team:
                continue
            if p.name in out:
                p.score[i] = 0.0

team_worth = bank
print("Existing players:")
for p in existing_players:
    p.display()
    team_worth += p.cost

#sc = [p.score[0] for p in players]
#plt.plot(sc,"ro")
#plt.show()
#sys.exit()    


wild_card = False
rik_onkel = False
spiss_rush = False


n_max_transf = 15

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
