import requests as req
import json
import sys 
import read_input as ri
from prettyplotting import PrettyPlot as pp
import time
import matplotlib.pyplot as plt
import numpy as np

url = "http://clubelo.com/Lillestrom"
t = time.time()
r = req.get(url)
print(r.content)
print(time.time()-t)
sys.exit()
#



            
player_id = 1
url = 'https://fantasy.premierleague.com/api/element-summary/' + str(player_id) + '/' 
r = req.get(url)
r = json.loads(r.content)

fixtures = r['fixtures']
history = r['history']
history_past = r['history_past']            

for e in history:
    
    print(e["total_points"],e["minutes"])
    print("")

