import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp

TEAMS = ['Kristiansund BK','Odd','Sandefjord','Molde','Bodø/Glimt','Mjøndalen','Lillestrøm','FK Haugesund','Sarpsborg 08','Brann','Strømsgodset','Rosenborg','Viking FK','Vålerenga','Stabæk','Tromsø']

def calculate_expected_score(players,prob_lose,games_played):

    a = 0.95    #Form weight
    #a = 1.0
    #a = 0.5
    
    for p in players:
        team = p.team
        
        try:
            p_lose = prob_lose[team]
        except KeyError:
            p.score = 0.0
            continue
        
        
        N_team = games_played[team]
        
        if p.minutes > 90:           
            score = a*p.form + (1-a) * (p.tot_points/N_team) #* p.minutes/(90*N_team) 
        else:
            score = p.form   
     
        factor = (1/3) / np.mean(p_lose) - 1.0    #1/3 is even match --> factor of 0. Use average over all games played this round
        factor *= 0.1
        
        #factor = 0.0
        
        p.score = score*(1+factor)

        N = len(p_lose)             #Number of games this round
        if N == 2:
            p.score *= 1.5
        elif N == 3:
            p.score *= 2
        elif N > 3:
            p.score *= 3
                    
print("")


n = 12
loc= f"eliteserien\\2021\\post_round_{n}\\"

games_played = {t:n+1 for t in TEAMS}
games_played['Kristiansund BK'] -= 1
games_played['Viking FK']       -= 1
games_played['Tromsø']          -= 1
games_played['Strømsgodset']    -= 2
games_played['Odd']             -= 2
games_played['Sarpsborg 08']    -= 2
games_played['Stabæk']          -= 3
games_played['Lillestrøm']      -= 3
games_played['Mjøndalen']       -= 3
games_played['FK Haugesund']    -= 3
games_played['Sandefjord']      -= 3

prob_lose = ri.get_lose_prob(loc+"match_probs.txt")

players = []

for pos in ["gkp","def","mid","fwd"]:
    
    file = loc+f"{pos}.txt"
    new_players = ri.read_position(file,pos)
    
    players += new_players
    
calculate_expected_score(players,prob_lose,games_played)

not_playing = {}
not_playing["Odd"] = []
not_playing["Bodø/Glimt"] = ["Sørli","Solbakken","Bjørkan"]
not_playing["Rosenborg"] = ["Zachariassen"]
not_playing["FK Haugesund"] = []

for team, out in not_playing.items():
    
    for p in players:
        if p.team != team:
            continue
        if p.name in out:
            p.score = 0.0
            
existing_player_list,bank = ri.read_existing_team(loc+"existing_team.txt")
print(existing_player_list)
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
    p.display()
    team_worth += p.cost
print("")

rik_onkel = False
spiss_rush = False

n_free_transf = 1

if rik_onkel:    
    team_worth = 10000
    n_free_transf = 15
    
if spiss_rush:
    for p in players:
        if p.position=="fwd":
            p.score *= 2
    
    
opt = pr.FantasyOptimizer(r"C:\CPLEX 20_10\cplex.exe")

opt.build_best_formation_model(players,budget = team_worth)
opt.add_existing_team(existing_players,n_free_transf=n_free_transf)
#opt.add_min_team_players("Rosenborg",1)  


opt.solve_model()
opt.display_results()
