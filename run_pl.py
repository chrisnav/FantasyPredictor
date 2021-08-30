import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt



TEAMS = ["Arsenal","Aston Villa","Brentford","Brighton","Burnley","Chelsea","Crystal Palace","Everton","Leeds","Leicester","Liverpool","Man Utd","Man City","Newcastle","Norwich","Southampton","Spurs","West Ham","Watford","Wolves"]

week = 2
loc = f"premier_league\\2021_2022\\"

players = []
for pos in ["gkp","def","mid","fwd"]:

    file = loc+f"game_week_{week}\\{pos}.txt"
    new_players = ri.read_position(file,pos)
    
    players += new_players
    

difficulty = ri.read_difficulty_rating(loc+"difficulty_rating.csv")

#for t,diff in difficulty.items():
#
#    alpha = [0.2*2**(-i) for i in range(len(diff))]
#    print(t,diff,sum(a*(3-d) for a,d in zip(alpha,diff)))
##plt.plot(alpha,"k")
##plt.show()
#sys.exit()

existing_player_list,bank = ri.read_existing_team(loc+f"game_week_{week}\\existing_team.txt")
print(bank)

existing_players = []
for player_id in existing_player_list:
    
    player_id = player_id.split("_")
    name = player_id[0]
    team = player_id[1]

    for p in players:                        
        if p.name == name and p.team == team:            
            existing_players.append(p)     
            break
            
    
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
    
    p.score = p.tot_points
    #print(p.name,p.tot_points)
    
    diff = [3-d for d in difficulty[p.team][week-1:]]  #1 is easy, 5 hard, 3 is neutral
    alpha = [0.2*2**(-i) for i in range(len(diff))]
        
    p.score *= 1.0 + sum(a*d for a,d in zip(alpha,diff))
    #p.score *= 1.0 + 0.2*(3-diff[week-1])

print("Existing players:")
for p in existing_players:                        
    p.display()
print("")

n_free_transf = 1

opt = pr.FantasyOptimizer(r"C:\My Stuff\CPLEX 20\cplex.exe")
opt.build_best_formation_model(players,budget = team_worth)
opt.add_existing_team(existing_players,n_free_transf=n_free_transf)

#opt.add_min_team_players("Liverpool",2)


opt.solve_model()
opt.display_results()
