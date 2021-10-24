import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt

def calculate_expected_score(players,home_teams,away_teams,difficulty,n_norm_week,future_week):
    
    lin_model = ri.read_linear_scoring_model("fdr_average_linear_model.txt")
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
        
        fdr = difficulty[p.team][0]
        if p.team in home_teams:
            is_home = 1
        elif p.team in away_teams:
            is_home = 0
        else:
            print("Team ",p.team,"is not in either list!")
            sys.exit()

            
        if len(p.score) == 0:
            prev_points = p.points_last_round
            average_points = p.tot_points/n_norm_week
        else:
            prev_points = p.score[-1]
            average_points = (p.tot_points+sum(p.score))/(n_norm_week+future_week)
            
        vals = [prev_points,average_points, p.minutes/n_norm_week,p.assists/n_norm_week,p.goals_conceded/n_norm_week,p.clean_sheets/n_norm_week]
        #vals = [prev_points,average_points, p.minutes/n_norm_week,p.assists/n_norm_week,p.goals_conceded/n_norm_week,p.clean_sheets/n_norm_week,is_home]
            
        mod = lin_model[pos][fdr]
        score = mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))
        
        p.score.append(score)

def calculate_expected_score_new(players,home_teams,away_teams,difficulty,prev_game_week,future_week):

    lin_model = ri.read_linear_scoring_model("fdr_big_linear_model.txt")
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
        
        if pos != 2:
            continue

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue        
        
        fdr = difficulty[p.team][0]
        if p.team in home_teams:
            is_home = 1
        elif p.team in away_teams:
            is_home = 0
        else:
            print("Team ",p.team,"is not in either list!")
            sys.exit()

        h = p.history
            
        average_points = (sum(h["total_points"])+sum(p.score))/(prev_game_week+future_week)
        
        average_min = sum(h["minutes"])/prev_game_week
        average_assist = sum(h["assists"])/prev_game_week
        average_goals_conceded = sum(h["goals_conceded"])/prev_game_week
        average_clean_sheets = sum(h["clean_sheets"])/prev_game_week
        average_goals_scored = sum(h["goals_scored"])/prev_game_week
        average_threat = sum(h["threat"])/prev_game_week
        average_creativity = sum(h["creativity"])/prev_game_week
        average_influence = sum(h["influence"])/prev_game_week
        average_ict = sum(h["ict_index"])/prev_game_week        
        
        if len(p.score) == 0:
            prev_points = h["total_points"][-1]
            prev_min = h["minutes"][-1]
            prev_assist = h["assists"][-1]
            prev_goals_conceded = h["goals_conceded"][-1]
            prev_clean_sheets = h["clean_sheets"][-1]
            prev_goals_scored = h["goals_scored"][-1]
            prev_threat = h["threat"][-1]
            prev_creativity = h["creativity"][-1]
            prev_influence = h["influence"][-1]
            prev_ict = h["ict_index"][-1]
        
        else:
            prev_points = p.score[-1]        
            prev_min = average_min
            prev_assist = average_assist
            prev_goals_conceded = average_goals_conceded
            prev_clean_sheets = average_clean_sheets
            prev_goals_scored = average_goals_scored
            prev_threat = average_threat
            prev_creativity = average_creativity
            prev_influence = average_influence
            prev_ict = average_ict
            
                        
        vals = [prev_points,average_points,prev_min,average_min,prev_assist,average_assist,prev_goals_conceded,average_goals_conceded,prev_clean_sheets,average_clean_sheets,prev_goals_scored,average_goals_scored,prev_threat,average_threat,prev_creativity,average_creativity,prev_influence,average_influence,prev_ict,average_ict]
            
        mod = lin_model[pos][fdr]
        score = mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))
        
        p.score.append(score)

def calculate_expected_score_points_model(players,home_teams,away_teams,difficulty,prev_game_week,future_week):
              
    lin_model = ri.read_linear_scoring_model("fdr_points_model.txt")
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

        if pos == 2:
            continue

        n_home = home_teams.count(p.team)
        n_away = away_teams.count(p.team)
        
        if n_home + n_away == 0:        
            p.score.append(0.0)
            continue
        
        fdr = difficulty[p.team][0]

        mod = lin_model[pos][fdr]
          
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
        
game_week = 9
    
url_base = "https://fantasy.premierleague.com/api/"
    
url_team = f"{url_base}entry/381388/event/{game_week-1}/picks/"
#url_team = f"{url_base}entry/143246/event/{game_week-1}/picks/"  #Sigurd

players,teams = ri.scrape_players(url_base)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

filename_history = f"premier_league\\2021_2022\\player_history_pl_{game_week-1}.txt"
try:
    ri.read_player_history(filename_history,players)
except FileNotFoundError:
    ri.create_player_history(url_base,filename_history,game_week-1)
    ri.read_player_history(filename_history,players)

not_playing = {}
#not_playing["Spurs"] = ["Son"]
#not_playing["Liverpool"] = ["Alexander-Arnold"]
#not_playing["Aston Villa"] = ["Watkins","Davis"]
not_playing["Everton"] = ["Doucouré"]
#not_playing["Leicester"] = ["Mendy"]

horizon = 3
for i in range(horizon):
    home_teams,away_teams,difficulty = ri.scrape_fixtures(url_base,teams,game_week+i)
    #calculate_expected_score(players,home_teams,away_teams,difficulty,game_week-1,i)    
    calculate_expected_score_new(players,home_teams,away_teams,difficulty,game_week-1,i)
    calculate_expected_score_points_model(players,home_teams,away_teams,difficulty,game_week-1,i)
    
    if i == 0:
        for p in players:
            if p.team in not_playing and p.name in not_playing[p.team]:
                p.score[0] = 0.0
            
team_worth = bank
for p in existing_players:
    team_worth += p.cost
    
print("Existing players:")
for p in existing_players:                        
    p.display()
print("")

print("Bank:",bank)
print("Total value:", team_worth)
print("Free transfers:",n_free_transf)
print("")

n_max_transf = 15

bench_boost = False
wild_card = False

if wild_card:    
    n_free_transf = 15
    n_max_transf = 15
    

#solver_path = r"C:\Users\Christian\CPLEX 20_10\cplex.exe"
solver_path = r"C:\My Stuff\CPLEX 20\cplex.exe"


opt = pr.MultiWeekFantasyOptimizer(solver_path)
opt.build_best_formation_model(players,horizon,team_worth,existing_players,n_free_transf,n_max_transf=n_max_transf)

#req_pl = [p for p in players if p.name in ["Ronaldo"]]
#opt.required_players(req_pl)
#opt.add_min_team_players("Liverpool",2)


opt.solve_model()
opt.display_results()
