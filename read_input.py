import predict as pr
import requests as req
import json
import sys
import time
import copy
from concurrent.futures import ThreadPoolExecutor
import threading

class Player(object):
    def __init__(self,name,cost,form,tot_points,minutes,assists,goals_conceded,clean_sheets,points_last_round,goals_scored,position,team,player_id = -1, real_name = ""):
        self.name = name
        self.cost = cost
        self.position = position
        self.team = team
        self.form = form
        self.tot_points = tot_points
        self.minutes = minutes
        self.assists = assists
        self.goals_conceded = goals_conceded
        self.clean_sheets = clean_sheets
        self.points_last_round = points_last_round
        self.goals_scored = goals_scored

        self.player_id = player_id
        
        if len(real_name) > 0:
            self.real_name = real_name
        else:
            self.real_name = name
        
        self.score = []     
        self.is_chosen = False
        self.is_cap = False
        self.on_pitch = False
        self.transferred = False
        
    def same_player(self,p):
        
        if (self.name not in p.real_name) and (p.name not in self.real_name):
            return False
        
        if self.position != p.position:
            return False
        
        if self.team != p.team:
            return False
                
        return True
        
    def display(self):
        print(f"Player: {self.name}, {self.team}, {self.position}. Cost {self.cost}, Score {self.score}")

def scrape_players(url_base):    
   
    url = f"{url_base}bootstrap-static/"
    
    r = req.get(url)
    r = json.loads(r.content)

    #rounds = r["events"]
    teams = r["teams"]

    team_code_to_name = {t["code"]:t["name"] for t in teams}
    
    elements = r["elements"] #element_type: 1 = gkp, 2 = def, 3 = mid, 4 = fwd
    players = []
    
    #print(elements[0])
    #
    #return
    
    for e in elements:

        et = e["element_type"]
        
        if et == 1:
            pos = "gkp"
        elif et == 2:
            pos = "def"
        elif et == 3:
            pos = "mid"
        elif et == 4:
            pos = "fwd"
        else:
            print("Unknown position ",et,"for player:")
            print(p)        
            continue
        
        #for k,v in e.items():
        #    print(k,v)
        #sys.exit()
        
        player_id = e["id"]
        real_name = e["first_name"]+" "+e["second_name"]
        name = e["web_name"]
        team = team_code_to_name[e["team_code"]]
        tot_points = float(e["total_points"])
        form = float(e["form"])
        minutes = float(e["minutes"])
        cost = float(e["now_cost"])*0.1
        assists = int(e["assists"])
        clean_sheets = int(e["clean_sheets"])
        goals_conceded = int(e["goals_conceded"])
        points_last_round = int(e["event_points"])
        goals_scored = int(e["goals_scored"])

        p = Player(name,cost,form,tot_points,minutes,assists,goals_conceded,clean_sheets,points_last_round,goals_scored,pos,team,player_id=player_id, real_name=real_name,)
        
        players.append(p)
    
    return players,teams
    
def scrape_fixtures(url_base,teams,week):

    team_id_to_name = {t["id"]:t["name"] for t in teams}

    difficulty = {t["name"]:[] for t in teams}
    home_teams = []
    away_teams = []
    
    url = f"{url_base}fixtures/"
    r = req.get(url)
    r = json.loads(r.content)

    for match in r:
        if match["event"] != week:
            continue     
            
        home = team_id_to_name[match["team_h"]]
        away = team_id_to_name[match["team_a"]]

        home_teams.append(home)
        away_teams.append(away)
        
        try:
            fdr_h = match["team_h_difficulty"]
            fdr_a = match["team_a_difficulty"]
            
            if home in difficulty.keys():
                difficulty[home].append(fdr_h)
            else:
                difficulty[home]= [fdr_h]
            
            if away in difficulty.keys():
                difficulty[away].append(fdr_a)
            else:
                difficulty[away]= [fdr_a]
                
        except KeyError:
            pass

        
    return home_teams,away_teams,difficulty
        
def scrape_exisitng_team(url_team,players):

    r = req.get(url_team)
    r = json.loads(r.content)

    existing_team = []
    for elemetn in r["picks"]:
        
        pid = elemetn["element"]
        
        for p in players:
            if p.player_id == pid:
                existing_team.append(p)
                break    
    
    if len(existing_team) != 15:
        print(f"All existing players not found, {len(existing_team)} players in list!")
        for p in existing_team:
            p.display()
        sys.exit()
        
    bank = r["entry_history"]["bank"]*0.1
    
    n_transfers = r["entry_history"]["event_transfers"]
    if n_transfers == 0:
        n_free_transfers = 2
    else:
        n_free_transfers = 1
    
    return existing_team, bank, n_free_transfers
    
def read_linear_scoring_model(file):
    
    linear_model = {i:{j:[] for j in range(2,6)} for i in range(1,5)}
    
    with open(file,"r") as f:
        lines = [l for l in f]
    
    for l in lines[1:]:
        l = l.split(";")
        
        position = int(l[0])
        fdr = int(l[1])
        const = float(l[2])
        variables = [float(v) for v in l[3:len(l)-1]]

        if fdr == -1:
            linear_model[position] = [const] + variables
        else:
            linear_model[position][fdr] = [const] + variables
        
    return linear_model

def player_summary_scrape(url_base,player_id,player_history,wait_time=0.1):            

    url = f"{url_base}element-summary/{player_id}/"
    r = req.get(url)
    status = r.status_code
    
    if status == 404:
        print("404: Unable to scrape player with id",player_id)
        return
    
    r = json.loads(r.content)
    
    player_history[player_id-1] = r["history"]
    
    time.sleep(wait_time)
    
    #fixtures = r['fixtures']
    #history = r['history']
    #history_past = r['history_past']     

def create_player_history(url_base,filename,game_week,wait_time=0.1):
    
    players,teams = scrape_players(url_base)
    N_players = len(players)

    team_id_to_name = {t["id"]:t["name"] for t in teams}


    player_history = [None for i in range(N_players)]

    t0 = time.time()

    with ThreadPoolExecutor() as threadPool:
    
        for player_id in range(1,N_players+1):
            
            threadPool.submit(player_summary_scrape,url_base,player_id,player_history,wait_time=wait_time)

    with ThreadPoolExecutor() as threadPool:
        
        for i,val in enumerate(player_history):
            
            if val is None:
                threadPool.submit(player_summary_scrape,url_base,i+1,player_history,wait_time=wait_time)
        
        
        
    t1 = time.time()

        
    with open(filename,"w",encoding="utf8") as f:

        for pid,history in enumerate(player_history):
            
            info = {}
            
            if history is None:
                print(pid,"is None!")
                player_summary_scrape(url_base,pid+1,player_history)                
                history = player_history[pid]
                
            for e in history:
                
                for key,val in e.items():
                    
                    if key in info:
                        info[key].append(val)
                    else:
                        info[key] = [val]
            
            rounds = info["round"]
            try:
                i = rounds.index(game_week)+1
            except ValueError:
                i = len(rounds)

            info["opponent_team"] = [team_id_to_name[j] for j in  info["opponent_team"]]                
            
            f.write(f"name;{players[pid].name};\n")
            f.write(f"position;{players[pid].position};\n")
            f.write(f"team;{players[pid].team};\n")

            for key,vals in info.items():
                f.write(f"{key};")
                for v in vals[:i]:
                    f.write(f"{v};")
                f.write("\n")    
                
            f.write("\n")

    
def read_player_history(file,players):

    with open(file,"r") as f:
        lines = [l for l in f]
        
    attr_dict = {}
    for l in lines:
        
        if l.count(";") == 0:

            pid = attr_dict["element"][0]
            p = None
            for player in players:
                if player.player_id == pid:
                    p = player
                    break
            
            if p is None:
                print("Did not find player with id",pid)
                sys.exit()
            
            p.history = copy.copy(attr_dict)
            
            attr_dict = {}
            continue
            
            
        l = l.split(";")
        
        attribute = l[0]
        
        if attribute in ["name","position","team"]:
            continue

        if attribute == "was_home" or attribute == "kickoff_time":
            vals = [v for v in l[1:] if v!="\n" and v != "None"]
        elif attribute == "round":
            vals = [int(v) for v in l[1:] if v!="\n" and v != "None"]
        else:
            vals = [float(v) for v in l[1:] if v!="\n" and v != "None"]
        
        attr_dict[attribute] = vals
        
        

    

    
    
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
                
                players.append(Player(name,cost,points,pos,team))
        
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
            
           
            p = Player(name,cost,form,tot_points,minutes,pos,team)
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