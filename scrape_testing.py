import requests as req
import json
import sys 
from prettyplotting import PrettyPlot as pp
import time
import matplotlib.pyplot as plt
import numpy as np
import read_input as ri

def elo_scrape():

    url = "http://clubelo.com/Lillestrom"
    t = time.time()
    r = req.get(url)
    print(r.content)
    print(time.time()-t)



def player_summary_scrape(url_base,player_id,player_history):            

    url = f"{url_base}element-summary/{player_id}/"
    r = req.get(url)
    status = r.status_code
    
    if status == 404:
        print("404: Unable to scrape player with id",player_id)
        return
    
    r = json.loads(r.content)

    player_history[player_id] = r["history"]
    print(r["history"])
    time.sleep(0.1)
    #fixtures = r['fixtures']
    #history = r['history']
    #history_past = r['history_past']            
    


    
    

#url_base = "https://fantasy.eliteserien.no/api/"
url_base = "https://fantasy.premierleague.com/api/"

for i in range(6,7):
    filename = f"player_history_pl_{i}.txt"
    ri.create_player_history(url_base,filename,i)

#player_summary_scrape(url_base,226,{})
sys.exit()

players,teams = ri.scrape_players(f"{url_base}bootstrap-static/")

        
ri.read_player_history(filename,players)

sys.exit()
