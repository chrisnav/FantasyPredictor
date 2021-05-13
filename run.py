import predict as pr
import sys

players = []

for pos in ["gkp","def","mid","fwd"]:
    
    file = f"C:\\Prog\\Fantasy\\eliteserien\\2021\\post_round_1\\{pos}.txt"
    new_players = pr.read_position(file,pos)
    
    players += new_players
    
#teams = [r"Bodø/Glimt","Vålerenga","Rosenborg","Kristiansund BK","Viking FK","Brann","Molde","Tromsø","Sandefjord","Odd"]
#players = [p for p in players if p.team in teams]


existing_player_dict,bank = pr.read_existing_team("eliteserien\\2021\\post_round_1\\existing_team.txt")
existing_players = []
for name,team in existing_player_dict.items():
    
    for p in players:
        if p.name == name and p.team == team:            
            existing_players.append(p)
    

team_worth = bank
for p in existing_players:
    p.display()
    team_worth += p.cost
print("")

opt = pr.FantasyOptimizer(r"C:\My Stuff\CPLEX 20\cplex.exe")

opt.build_basic_model(players,existing_players=existing_players,budget = team_worth)

opt.solve_model()
opt.display_results()

print(opt.model.n_keep.value,opt.model.n_changes.value)