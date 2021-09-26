import statsmodels.api as sm
import numpy as np
import sys
import matplotlib.pyplot as plt 

def get_player_stats(season):

    filename = fr"premier_league\statistics\{season}\fixtures.csv"
    with open(filename, "r",encoding="latin") as f:
        lines = [l for l in f]
        
    header = lines[0].split(",")
    id_index = header.index("id")
    a_fdr_index = header.index("team_a_difficulty")
    h_fdr_index = header.index("team_h_difficulty")    
    stats_index = header.index("stats")
    n = len(header)

    if id_index > stats_index or a_fdr_index < stats_index or h_fdr_index < stats_index:
        print("OOPS!",id_index,a_fdr_index,h_fdr_index,stats_index)


    events = {}

    for l in lines[1:]:
        l = l.split(",")
            
        skip = len(l)-n

        e = {}
        #e["week"] = int(l[1])
        event_id = int(l[id_index])
        #e["team_a"] = int(l[9])
        #e["team_h"] = int(l[11])
        e["team_h_fdr"] = int(l[h_fdr_index+skip])
        e["team_a_fdr"] = int(l[a_fdr_index+skip])
        
        events[event_id]=e

        
    filename = fr"premier_league\statistics\{season}\gws\merged_gw.csv"
    with open(filename, "r",encoding="latin") as f:
        lines = [l for l in f]    
        
    header = lines[0].split(",")
    id_index = header.index("element")
    e_id_index = header.index("fixture")
    min_index = header.index("minutes")
    point_index = header.index("total_points")      
    assist_index = header.index("assists")      
    clean_sheets_index = header.index("clean_sheets")      
    goals_conceded_index = header.index("goals_conceded")      
    goals_scored_index = header.index("goals_scored")      
    home_index = header.index("was_home")      

        
    players = {}
    for l in lines[1:]:
        
        l = l.split(",")
        
        player_id = int(l[id_index])    
        event_id = int(l[e_id_index])
        minutes = int(l[min_index])
        points = int(l[point_index])
        assists = int(l[assist_index])
        goals_conceded = int(l[goals_conceded_index])
        clean_sheets = int(l[clean_sheets_index])
        goals_scored = int(l[goals_scored_index])

        if l[home_index].lower() == "true":
            is_home = 1
            fdr = events[event_id]["team_h_fdr"]
        elif l[home_index].lower() == "false":
            is_home = 0
            fdr = events[event_id]["team_a_fdr"]
        else:
            print("ooops:",l[home_index])
            sys.exit()
            
        if player_id not in players.keys():
            players[player_id] = {"points":[],"fdr":[],"minutes":[],"assists":[],"goals_conceded":[],"clean_sheets":[],"goals_scored":[],"is_home":[]}
            
        players[player_id]["points"].append(points)
        players[player_id]["assists"].append(assists)
        players[player_id]["goals_conceded"].append(goals_conceded)
        players[player_id]["clean_sheets"].append(clean_sheets)
        players[player_id]["goals_scored"].append(goals_scored)
        players[player_id]["is_home"].append(is_home)

        players[player_id]["fdr"].append(fdr)
        players[player_id]["minutes"].append(minutes)
        
    filename = fr"premier_league\statistics\{season}\players_raw.csv"
    with open(filename, "r",encoding="latin") as f:
        lines = [l for l in f]    
        
    header = lines[0].split(",")
    id_index = header.index("id")     
    position_index = header.index("element_type")              
        
    for l in lines[1:]:
        l = l.split(",")
        
        player_id = int(l[id_index])    
        position = int(l[position_index])        
        
        p = players[player_id]
        p["position"] = position        
        
        
    return players

def create_fdr_model(players):

    form_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_inf = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    minutes = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    assists = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_conceded = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    clean_sheets = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_scored = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    is_home = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    score = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 3:
                continue
                
            fdr = p["fdr"][i]      
            form_1[fdr][pos].append(np.mean(p["points"][i-1]))            
            form_inf[fdr][pos].append(np.mean(p["points"][:i]))            
            minutes[fdr][pos].append(np.mean(p["minutes"][:i]))       
            assists[fdr][pos].append(np.mean(p["assists"][:i]))       
            goals_conceded[fdr][pos].append(np.mean(p["goals_conceded"][:i]))       
            clean_sheets[fdr][pos].append(np.mean(p["clean_sheets"][:i]))       
            goals_scored[fdr][pos].append(np.mean(p["goals_scored"][:i]))       
            is_home[fdr][pos].append(p["is_home"][i])

            score[fdr][pos].append(p["points"][i])

    print("")

    fitted_model = {}
    #var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets","average_goals_scored"]
    var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets","is_home"]

    for i in range(1,5):
        
        fitted_model[i] = {}
        
        print("Position:",i)
        
        for j in range(2,6):
            print("FDR:",j)

            y = np.array(score[j][i])
                    
                    
            x1 = np.array(form_1[j][i])
            x2 = np.array(form_inf[j][i])
            x3 = np.array(minutes[j][i])
            x4 = np.array(assists[j][i])
            x5 = np.array(goals_conceded[j][i])
            x6 = np.array(clean_sheets[j][i])
            x7 = np.array(is_home[j][i])
                    
            all_x = [x1,x2,x3,x4,x5,x6,x7]

            x = np.array(all_x).T             
            
            x = sm.add_constant(x)
            mod = sm.OLS(y,x)
            fit = mod.fit()       

            p_values = fit.pvalues

            alpha = 0.05
            worst = []
            coeffs = list(fit.params)
            rsq = fit.rsquared            

            while max(p_values) > alpha:  
            
                #print("Refitting:",list(p_values))
                worst.append(np.argmax(p_values))

                new_x = np.array([var for k,var in enumerate(all_x) if k+1 not in worst]).T

                if 0 not in worst:
                    new_x = sm.add_constant(new_x)
                mod = sm.OLS(y,new_x)
                fit = mod.fit()  
                                    
                new_p_values = fit.pvalues
                rsq = fit.rsquared                
                new_coeffs = fit.params

                l = 0
                for k,v in enumerate(coeffs):
                    if k in worst:
                        coeffs[k] = 0.0
                        p_values[k] = 0.0
                    else:
                        coeffs[k] = new_coeffs[l]
                        p_values[k] = new_p_values[l]
                        l += 1                                                
                
            print(rsq)
            for name,c in zip(var_names,coeffs):
                print(name,c)
            print("")

            fitted_model[i][j] = coeffs
            
            #k = 1
            #for m in range(len(all_x)):
            #    if m+1 in worst:
            #        print(f"x{m+1} not part of fit")
            #        continue           
            #        
            #    fig = plt.figure(figsize=(12,8))
            #    fig = sm.graphics.plot_regress_exog(fit, f'x{k}', fig=fig)
            #    plt.show()        
            #    k += 1        
        
        
        
        print("")

    with open("fdr_linear_model.txt","w") as f:
        
        f.write("Position;FDR;")
        for name in var_names:
            f.write(name+";")
        f.write("\n")

        for i, fm in fitted_model.items():
            for j,coeffs in fm.items():
                f.write(str(i)+";"+str(j)+";")
                for c in coeffs:
                    f.write(str(c)+";")
                f.write("\n")

def create_simple_model(players):

    form_1 = {i:[] for i in range(1,5)}
    form_inf = {i:[] for i in range(1,5)}
    minutes = {i:[] for i in range(1,5)}
    assists = {i:[] for i in range(1,5)}
    goals_conceded = {i:[] for i in range(1,5)}
    clean_sheets = {i:[] for i in range(1,5)}
    goals_scored = {i:[] for i in range(1,5)}
    is_home = {i:[] for i in range(1,5)}    

    score = {i:[] for i in range(1,5)}    

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 3:
                continue
                
            fdr = p["fdr"][i]      
            form_1[pos].append(p["points"][i-1])            
            form_inf[pos].append(np.mean(p["points"][:i]))            
            minutes[pos].append(np.mean(p["minutes"][:i]))       
            assists[pos].append(np.mean(p["assists"][:i]))   
            goals_conceded[pos].append(np.mean(p["goals_conceded"][:i]))   
            clean_sheets[pos].append(np.mean(p["clean_sheets"][:i]))   
            goals_scored[pos].append(np.mean(p["goals_scored"][:i]))   
            is_home[pos].append(p["is_home"][i])
            
            score[pos].append(p["points"][i])

    print("")

    fitted_model = {}

    #var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets","average_goals_scored"]
    var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets","is_home"]

    for i in range(1,5):
        
        print("Position:",i)

        y = np.array(score[i])
                
        x1 = np.array(form_1[i])
        x2 = np.array(form_inf[i])
        x3 = np.array(minutes[i])
        x4 = np.array(assists[i])
        x5 = np.array(goals_conceded[i])
        x6 = np.array(clean_sheets[i])
        x7 = np.array(is_home[i])
                
        all_x = [x1,x2,x3,x4,x5,x6,x7]

        x = np.array(all_x).T

        x = sm.add_constant(x)
        mod = sm.OLS(y,x)
        fit = mod.fit()       

        p_values = fit.pvalues

        alpha = 0.05
        worst = []
        coeffs = list(fit.params)
        rsq = fit.rsquared            

        while max(p_values) > alpha:  
        
            #print("Refitting:",list(p_values))
            worst.append(np.argmax(p_values))

            new_x = np.array([var for k,var in enumerate(all_x) if k+1 not in worst]).T

            if 0 not in worst:
                new_x = sm.add_constant(new_x)
            mod = sm.OLS(y,new_x)
            fit = mod.fit()  
                                
            new_p_values = fit.pvalues
            rsq = fit.rsquared                
            new_coeffs = fit.params

            l = 0
            for k,v in enumerate(coeffs):
                if k in worst:
                    coeffs[k] = 0.0
                    p_values[k] = 0.0
                else:
                    coeffs[k] = new_coeffs[l]
                    p_values[k] = new_p_values[l]
                    l += 1
                
            #sys.exit()
        
        print(rsq)
        for name,c in zip(var_names,coeffs):
            print(name,c)
        print("")
        
        #k = 1
        #for i in range(len(all_x)):
        #    if i+1 in worst:
        #        print(f"{var_names[i+1]} not part of fit")
        #        continue           
        #        
        #    fig = plt.figure(figsize=(12,8))
        #    fig = sm.graphics.plot_regress_exog(fit, f'x{k}', fig=fig)
        #    plt.show()        
        #    k += 1
        
        
        #fig = plt.figure(figsize=(12,8))
        #fig = sm.graphics.plot_regress_exog(fit, f'x2', fig=fig)
        #plt.show()                
            

    
        fitted_model[i] = coeffs
        
        
        print("")

    with open("simple_linear_model.txt","w") as f:
        
        f.write("Position;FDR;")
        for name in var_names:
            f.write(name+";")
        f.write("\n")
        
        for i, coeffs in fitted_model.items():
            f.write(str(i)+";-1;")
            for c in coeffs:
                f.write(str(c)+";")
            f.write("\n")




seasons = ["2018-19","2019-20","2020-21"]

players = {}
for i,season in enumerate(seasons):
    print("reading season ",season)
    
    p = get_player_stats(season)

    for k,v in p.items():
        players[k+i*10000] = v

    

create_fdr_model(players)    
#create_simple_model(players)
