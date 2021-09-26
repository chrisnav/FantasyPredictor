import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt

def calculate_expected_score(players,home_teams,away_teams,difficulty,n_norm_week,future_week):

    #for p in players:
    #
    #    p.score = p.form #p.tot_points
    #    #print(p.name,p.tot_points)
    #    
    #    diff = [3-d for d in difficulty[p.team][week-1:]]  #1 is easy, 5 hard, 3 is neutral
    #    alpha = [0.2*2**(-i) for i in range(len(diff))]
    #        
    #    p.score *= 1.0 + sum(a*d for a,d in zip(alpha,diff))
    #    #p.score *= 1.0 + 0.2*(3-diff[week-1])
    
    lin_model = ri.read_linear_scoring_model("fdr_linear_model.txt")
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
            
        vals = [prev_points,average_points, p.minutes/n_norm_week,p.assists/n_norm_week,p.goals_conceded/n_norm_week,p.clean_sheets/n_norm_week,is_home]
            
        mod = lin_model[pos][fdr]
        score = mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))
        
        p.score.append(score)

game_week = 6
    
url = "https://fantasy.premierleague.com/api/bootstrap-static/"   
url_team = f"https://fantasy.premierleague.com/api/entry/381388/event/{game_week-1}/picks/"
#url_team = f"https://fantasy.premierleague.com/api/entry/143246/event/{game_week-1}/picks/"  #Sigurd
url_fix = "https://fantasy.premierleague.com/api/fixtures/"

players,teams = ri.scrape_players(url)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

not_playing = {}
not_playing["Spurs"] = ["Son"]
#not_playing["Liverpool"] = ["Robertson"]
#not_playing["Aston Villa"] = ["Watkins","Davis"]
not_playing["Everton"] = ["Delph"]
not_playing["Leicester"] = ["Mendy"]

horizon = 4
for i in range(horizon):
    home_teams,away_teams,difficulty = ri.scrape_fixtures(url_fix,teams,game_week+i)
    calculate_expected_score(players,home_teams,away_teams,difficulty,game_week-1,i)

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
free_hit = False

if free_hit:    
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
