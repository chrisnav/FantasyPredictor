import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp

TEAMS = ["Arsenal","Aston Villa","Brentford","Brighton","Burnley","Chelsea","Crystal Palace","Everton","Leeds","Leicester","Liverpool","Man Utd","Man City","Newcastle","Norwich","Southampton","Spurs","West Ham","Watford","Wolves"]

loc = f"premier_league\\2021_2022\\before_season_start\\"

players = []
for pos in ["gkp","def","mid","fwd"]:

    file = loc+f"{pos}.txt"
    new_players = ri.read_position(file,pos)
    
    players += new_players
    
not_playing = {}
not_playing["Liverpool"] = ["Robertson"]
not_playing["Aston Villa"] = ["Watkins","Davis"]
not_playing["Everton"] = ["Calvert-Lewin"]
    
for p in players:
    
    p.score = p.tot_points
    
    if p.team in not_playing and p.name in not_playing[p.team]:
        p.score = 0.0



team_worth = 100

opt = pr.FantasyOptimizer(r"C:\My Stuff\CPLEX 20\cplex.exe")
opt.build_best_formation_model(players,budget = team_worth)
opt.add_min_team_players("Liverpool",2)


opt.solve_model()
opt.display_results()
