import predict as pr

def read_team(team_file,team):

    ##This is for PL fantasy

    with open(team_file,"r",encoding="utf-8") as f:
        lines = [l for l in f]
    
    pos = ""
    name = ""
    cost = -1
    players = []
    
    for l in lines:
        
        if len(l) < 3:
            continue
        
        if "Goalkeepers" in l:
            pos = "gkp"
            continue
        elif "Defenders" in l:
            pos = "def"
            continue
        elif "Midfielders" in l:
            pos = "mid"
            continue
        elif "Forwards" in l:
            pos  = "fwd"
            continue

        if pos in l:
            continue
        l_split = l.split()
        
        if len(l_split) > 1:
            try:
                cost = float(l_split[0])
                points = float(l_split[1])
                
                players.append(pr.Player(name,cost,points,pos,team))
        
                name = ""
                cost = -1                                
                continue
            except ValueError:
                pass
        
        name = l.strip()
                
    return players
        
def read_position(position_file,pos):
    
    ##This is for Eliteserien fantasy
    
    pos = pos.lower()
    
    players = []

    with open(position_file,"r",encoding="utf-8") as f:
        lines = [l for l in f]
    
    team = ""
    name = ""
    team_short = ""
    cost = -1
    
    for l in lines:
        
        if len(l) < 2 or "View player information" in l:
            continue
        
        if len(team) == 0:
            team = l.strip()
            continue
        
        if len(name) == 0:
            name = l.strip()
            continue
            
        if len(team_short) == 0:
            team_short = l.strip()
            continue
        
        if cost == -1:
            l_split = l.split()
            cost = float(l_split[0])
            form = float(l_split[2])
            tot_points = float(l_split[3])
            minutes = float(l_split[4])
            
           
            p = pr.Player(name,cost,form,tot_points,minutes,pos,team)
            players.append(p)
            
            team = ""
            name = ""
            team_short = ""
            cost = -1
                
    return players        
    
def read_existing_team(file):
    
    with open(file,"r",encoding="utf-8") as f:
        lines = [l for l in f]
        
    bank_line = lines[0].split(":")
    bank = float(bank_line[1])
        
    players = []
    name = ""
    team = ""
    team_short = ""

    for l in lines[1:]:
        if len(l) < 2:
            continue        
        
        if len(team) == 0:
            team = l.strip()
            continue
        
        if len(name) == 0:
            name = l.strip()
            continue
            
        if len(team_short) == 0:
            team_short = l.strip()
            continue
            
        else:
            
            players.append(name+"_"+team)
            
            name = ""
            team = ""     
            team_short = ""
            
    return players,bank
        
def read_difficulty_rating(file,week = -1):
    
    difficulty = {}
    
    with open(file,"r") as f:
        lines = [l for l in f]
    
    for l in lines[1:]:
        l = l.split(",")
                
        team = l[0]
        if week == -1:
            difficulty[team] = [int(val) for val in l[1:]]
        else:
            difficulty[team] = int(l[week])
            
        
    return difficulty
    
        
def create_player_input(data_dir, prob_lose, games_per_team,  read_prev_team = True):

    players = []
    
    #Read all available players
    for pos in ["gkp","def","mid","fwd"]:
        
        file = data_dir+f"{pos}.txt"
        new_players = read_position(file,pos)
        
        players += new_players
        
    #Calculate an expected score for each player
    for p in players:
        team = p.team
        
        N = games_per_team[team]        

        score = 0.9*p.form + 0.1*p.tot_points/N    #90% form, 10% average total season points
        
        p_lose = prob_lose[team]         #Team loss probability according to odds        
        factor = (1/3) / p_lose - 1.0    #1/3 is even match --> factor of 0
        factor *= 0.1                   
        
        p.score = score*(1+factor)

    existing_players = []
    total_funds = 100.0
    
    if read_prev_team:
    
        existing_player_dict,bank = read_existing_team(data_dir+"existing_team.txt") 
        
        for name,team in existing_player_dict.items():
            
            for p in players:
                if p.name == name and p.team == team:            
                    existing_players.append(p)
            
        total_funds = bank + sum(p.cost for p in existing_players)
        
        
def get_lose_prob(filename):
    
    prob_lose = {}

    with open(filename,"r",encoding="utf-8") as f:
        lines = [l for l in f]
        
    for l in lines:
        
        l = l.split(",")
        home = l[0]
        away = l[1]
        H = float(l[2])
        U = float(l[3])
        B = float(l[4])
        
        p_tot = 1.0/H + 1.0/U + 1.0/B
        
        p_h_lose = (1.0/B)/p_tot
        p_a_lose = (1.0/H)/p_tot
        
        if home in prob_lose:
            prob_lose[home].append(p_h_lose)
        else:
            prob_lose[home] = [p_h_lose]

        if away in prob_lose:
            prob_lose[away].append(p_a_lose)
        else:
            prob_lose[away] = [p_a_lose]
            
    return prob_lose        