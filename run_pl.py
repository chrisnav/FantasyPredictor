import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp

TEAMS = ["Arsenal","Aston Villa","Brentford","Brighton","Burnley","Chelsea","Crystal Palace","Everton","Leeds","Leicester","Liverpool","Man Utd","Man City","Newcastle","Norwich","Southampton","Spurs","West Ham","Watford","Wolves"]

week = 1
loc = f"premier_league\\2021_2022\\"

players = []
for pos in ["gkp","def","mid","fwd"]:

    file = loc+f"game_week_{week}\\{pos}.txt"
    new_players = ri.read_position(file,pos)
    
    players += new_players
    

difficulty = ri.read_difficulty_rating(loc+"difficulty_rating.csv")


    
not_playing = {}
not_playing["Liverpool"] = ["Robertson"]
not_playing["Aston Villa"] = ["Watkins","Davis"]
not_playing["Everton"] = ["Calvert-Lewin"]
    
for p in players:
    
    if p.team in not_playing and p.name in not_playing[p.team]:
            p.score = 0.0
            continue    
    
    p.score = p.tot_points
    
    diff = [3-d for d in difficulty[p.team][week-1:]]  #1 is easy, 5 hard, 3 is neutral
    alpha = [0.2*2**(-i) for i in range(len(diff))]
        
    p.score *= 1.0 + sum(a*d for a,d in zip(alpha,diff))


team_worth = 100

opt = pr.FantasyOptimizer(r"C:\My Stuff\CPLEX 20\cplex.exe")
opt.build_best_formation_model(players,budget = team_worth)
opt.add_min_team_players("Liverpool",2)


opt.solve_model()
opt.display_results()
