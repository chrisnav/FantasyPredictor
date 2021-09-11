import predict as pr
import read_input as ri
import sys
import numpy as np
from prettyplotting import PrettyPlot as pp
import matplotlib.pyplot as plt

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
            
        N = len(p_lose)             #Number of games this round
        if N == 0:
            p.score = 0.0
            continue
        
        N_team = games_played[team]
        
        if p.minutes > 3*90:           
            score = a*p.form + (1-a) * (p.tot_points/N_team) #* p.minutes/(90*N_team) 
        else:
            score = p.form*0.5

        factor = (1/3) / np.mean(p_lose) - 1.0    #1/3 is even match --> factor of 0. Use average over all games played this round
        factor *= 0.1
        
        #factor = 0.0
        
        p.score = score*(1+factor)


        if N == 2:
            p.score *= 1.5
        elif N == 3:
            p.score *= 2
        elif N > 3:
            p.score *= 3
            
            
def calculate_score(players,week):
              
    lin_model = ri.read_linear_scoring_model("simple_linear_model.txt")
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

        mod = lin_model[pos]
        vals = [p.points_last_round,p.tot_points/week,p.minutes/week,p.assists/week,p.goals_conceded/week,p.clean_sheets/week]
        score = mod[0] + sum(v*c for v,c in zip(vals,mod[1:]))

        p.score = score
            
game_week = 18

url = "https://fantasy.eliteserien.no/api/bootstrap-static/"     
url_team = f"https://fantasy.eliteserien.no/api/entry/29209/event/{game_week-1}/picks/"

players,teams = ri.scrape_players(url)
existing_players,bank,n_free_transf = ri.scrape_exisitng_team(url_team,players)

games_played = {t["name"]:game_week-1 for t in teams}

prob_lose = {t["name"]:[1/3] for t in teams}
#prob_lose["Molde"] = []
#prob_lose["Sarpsborg 08"] = []
    
#calculate_expected_score(players,prob_lose,games_played)
calculate_score(players,game_week-1)


not_playing = {}
not_playing["Odd"] = ["Bakenga"]
not_playing["Bodø/Glimt"] = ["Sørli"]
not_playing["Rosenborg"] = ["Zachariassen"]
not_playing["FK Haugesund"] = ["Desler"]
not_playing["Vålerenga"] = ["Dønnum"]
not_playing["Mjøndalen"] = ["Thomas"]
not_playing["Viking FK"] = ["Haugen","Tripic"]
not_playing["Stabæk"] = ["Edvardsen"]

for team, out in not_playing.items():
    
    for p in players:
        if p.team != team:
            continue
        if p.name in out:
            p.score = 0.0
                
team_worth = bank
print("Existing players:")
for p in existing_players:
    p.display()
    team_worth += p.cost

print("")
print("Bank:",bank)
print("Total value:",team_worth)
print("Free transfers:",n_free_transf)
print("")

rik_onkel = False
spiss_rush = False


if rik_onkel:    
    team_worth = 10000
    n_free_transf = 15
    
if spiss_rush:
    for p in players:
        if p.position=="fwd":
            p.score *= 2
    

#solver_path = r"C:\Users\Christian\CPLEX 20_10\cplex.exe"
solver_path = r"C:\My Stuff\CPLEX 20\cplex.exe"

opt = pr.FantasyOptimizer(solver_path)
opt.build_best_formation_model(players,budget = team_worth)
opt.add_existing_team(existing_players,n_free_transf=n_free_transf)
#opt.add_min_team_players("Rosenborg",1)  


opt.solve_model()
opt.display_results()
