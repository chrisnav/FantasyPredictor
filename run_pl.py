import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt



TEAMS = ["Arsenal","Aston Villa","Brentford","Brighton","Burnley","Chelsea","Crystal Palace","Everton","Leeds","Leicester","Liverpool","Man Utd","Man City","Newcastle","Norwich","Southampton","Spurs","West Ham","Watford","Wolves"]

week = 4
loc = f"premier_league\\2021_2022\\"
    
url = "https://fantasy.premierleague.com/api/bootstrap-static/"   
url_team = f"https://fantasy.premierleague.com/api/entry/381388/event/{week-1}/picks/"
url_fdr = "https://fantasy.premierleague.com/api/fixtures/"

players,teams = ri.scrape_players(url)
difficulty = ri.scrape_difficulty_rating(url_fdr,teams)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

    
team_worth = bank
for p in existing_players:
    team_worth += p.cost
    
not_playing = {}
#not_playing["Liverpool"] = ["Robertson"]
#not_playing["Aston Villa"] = ["Watkins","Davis"]
#not_playing["Everton"] = ["Calvert-Lewin"]
    
for p in players:
    
    if p.team in not_playing and p.name in not_playing[p.team]:
        p.score = 0.0
        continue    
    
    p.score = p.form #p.tot_points
    #print(p.name,p.tot_points)
    
    diff = [3-d for d in difficulty[p.team][week-1:]]  #1 is easy, 5 hard, 3 is neutral
    alpha = [0.2*2**(-i) for i in range(len(diff))]
        
    p.score *= 1.0 + sum(a*d for a,d in zip(alpha,diff))
    #p.score *= 1.0 + 0.2*(3-diff[week-1])

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
    

solver_path = r"C:\Users\Christian\CPLEX 20_10\cplex.exe"
#solver_path = r"C:\My Stuff\CPLEX 20\cplex.exe"

opt = pr.FantasyOptimizer(solver_path)
opt.build_best_formation_model(players,budget = team_worth,bench_boost=bench_boost)
opt.add_existing_team(existing_players,n_free_transf=n_free_transf,n_max_transf=n_max_transf)


#opt.add_min_team_players("Liverpool",2)


opt.solve_model()
opt.display_results()
