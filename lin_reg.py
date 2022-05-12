import statsmodels.api as sm
from scipy import stats
import numpy as np
import sys
import matplotlib.pyplot as plt 
from sklearn.linear_model import LinearRegression
import pandas as pd

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
    influence_index = header.index("influence")      
    creativity_index = header.index("creativity")      
    threat_index = header.index("threat")      
    ict_index = header.index("ict_index")      
    opponent_index = header.index("opponent_team")      
    

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
        influence = float(l[influence_index])
        creativity = float(l[creativity_index])
        threat = float(l[threat_index])
        ict = float(l[ict_index])
        opponent = int(l[opponent_index])

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
            players[player_id] = {"points":[],"fdr":[],"minutes":[],"assists":[],"goals_conceded":[],"clean_sheets":[],"goals_scored":[],"is_home":[],"threat":[],"influence":[],"creativity":[],"ict":[],"opponent":[]}
            
        players[player_id]["points"].append(points)
        players[player_id]["assists"].append(assists)
        players[player_id]["goals_conceded"].append(goals_conceded)
        players[player_id]["clean_sheets"].append(clean_sheets)
        players[player_id]["goals_scored"].append(goals_scored)
        players[player_id]["is_home"].append(is_home)
        players[player_id]["threat"].append(threat)
        players[player_id]["influence"].append(influence)
        players[player_id]["creativity"].append(creativity)
        players[player_id]["ict"].append(ict)
        players[player_id]["opponent"].append(opponent)

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

def create_big_fdr_model(players,save=False):

    form_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    minutes_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    minutes_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    minutes_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    minutes_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    assists_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    assists_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    assists_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    assists_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    goals_conceded_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_conceded_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_conceded_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_conceded_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    clean_sheets_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    clean_sheets_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    clean_sheets_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    clean_sheets_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    goals_scored_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_scored_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_scored_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    goals_scored_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    is_home = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    
    threat_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    threat_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    threat_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    threat_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    creativity_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    creativity_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    creativity_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    creativity_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    influence_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    influence_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    influence_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    influence_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    ict_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    ict_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    ict_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    ict_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}    
    
    score = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 4:
                continue
                
            fdr = p["fdr"][i]      
            form_1[fdr][pos].append(p["points"][i-1])            
            form_2[fdr][pos].append(np.mean(p["points"][:i]))
   

            minutes_1[fdr][pos].append(p["minutes"][i-1]) 
            minutes_2[fdr][pos].append(np.mean(p["minutes"][:i])) 
            
            assists_1[fdr][pos].append(p["assists"][i-1])
            assists_2[fdr][pos].append(np.mean(p["assists"][:i]))
            
            goals_conceded_1[fdr][pos].append(p["goals_conceded"][i-1])       
            goals_conceded_2[fdr][pos].append(np.mean(p["goals_conceded"][:i]))        

            clean_sheets_1[fdr][pos].append(p["clean_sheets"][i-1])       
            clean_sheets_2[fdr][pos].append(np.mean(p["clean_sheets"][:i]))  
            
            goals_scored_1[fdr][pos].append(p["goals_scored"][i-1])       
            goals_scored_2[fdr][pos].append(np.mean(p["goals_scored"][:i]))   
            
            is_home[fdr][pos].append(p["is_home"][i])
            
            threat_1[fdr][pos].append(p["threat"][i-1])
            threat_2[fdr][pos].append(np.mean(p["threat"][:i]))

            creativity_1[fdr][pos].append(p["creativity"][i-1])
            creativity_2[fdr][pos].append(np.mean(p["creativity"][:i]))

            influence_1[fdr][pos].append(p["influence"][i-1])
            influence_2[fdr][pos].append(np.mean(p["influence"][:i]))

            ict_1[fdr][pos].append(p["ict"][i-1])
            ict_2[fdr][pos].append(np.mean(p["ict"][:i]))       

            score[fdr][pos].append(p["points"][i])

    print("")

    fitted_model = {}
    var_names = ["const"]#,"points_last","points_average","minutes_last","minutes_average"]
    var_names += [f"points_{i+1}" for i in range(2)]
    var_names += [f"minutes_{i+1}" for i in range(2)]
    #var_names += ["is_home"]

    var_names += [f"assists_{i+1}" for i in range(2)]
    var_names += [f"goals_conceded_{i+1}" for i in range(2)]
    var_names += [f"clean_sheets_{i+1}" for i in range(2)]
    var_names += [f"goals_scored_{i+1}" for i in range(2)]
    var_names += [f"threat_{i+1}" for i in range(2)]
    var_names += [f"creativity_{i+1}" for i in range(2)]
    var_names += [f"influence_{i+1}" for i in range(2)]
    var_names += [f"ict_{i+1}" for i in range(2)]


    for i in range(1,5):
        
        fitted_model[i] = {}
        
        print("Position:",i)
        
        for j in range(2,6):
            print("FDR:",j)

            y = np.array(score[j][i])
                    
            all_x = []
                    
            all_x.append(np.array(form_1[j][i]))
            all_x.append(np.array(form_2[j][i]))
             
            all_x.append(np.array(minutes_1[j][i]))
            all_x.append(np.array(minutes_2[j][i]))
            
            #if j != 5:
            #    all_x.append(np.array(is_home[j][i]))

            
            all_x.append(np.array(assists_1[j][i]))
            all_x.append(np.array(assists_2[j][i]))
            
            all_x.append(np.array(goals_conceded_1[j][i]))
            all_x.append(np.array(goals_conceded_2[j][i]))
            
            all_x.append(np.array(clean_sheets_1[j][i]))
            all_x.append(np.array(clean_sheets_2[j][i]))
            
            all_x.append(np.array(goals_scored_1[j][i]))
            all_x.append(np.array(goals_scored_2[j][i]))
            
            
            all_x.append(np.array(threat_1[j][i]))
            all_x.append(np.array(threat_2[j][i]))
            
            all_x.append(np.array(creativity_1[j][i]))
            all_x.append(np.array(creativity_2[j][i]))           
            
            all_x.append(np.array(influence_1[j][i]))
            all_x.append(np.array(influence_2[j][i]))            
            
            all_x.append(np.array(ict_1[j][i]))
            all_x.append(np.array(ict_2[j][i]))

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
                
            #print(var_names,coeffs)
            print(rsq)
            for name,c in zip(var_names,coeffs):
                print(name,c)
            print("")

            fitted_model[i][j] = coeffs
            
            #q = 1
            #for m in range(len(all_x)):
            #    if m+1 in worst:
            #        print(f"x{m+1} not part of fit")
            #        continue           
            #        
            #    fig = plt.figure(figsize=(12,8))
            #    fig = sm.graphics.plot_regress_exog(fit, f'x{q}', fig=fig)
            #    plt.show()        
            #    q += 1        
        
        
        
        print("")
    
    if save:
        with open("fdr_big_linear_model.txt","w") as f:
            
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

def create_average_fdr_model(players,save=False):

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
    #var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets","is_home"]
    var_names = ["const","points_last_game","average_points","average_minutes","average_assists","average_goals_conceded","average_clean_sheets"]

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
                    
            #if j != 5:
            #    all_x = [x1,x2,x3,x4,x5,x6,x7]
            #else:
            #    all_x = [x1,x2,x3,x4,x5,x6]
            all_x = [x1,x2,x3,x4,x5,x6]
            
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
    
    if save:
        with open("fdr_average_linear_model.txt","w") as f:
            
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

def test_model(players,save=False,plot=False):

    form_1 = {i:[] for i in range(1,5)}
    form_2 = {i:[] for i in range(1,5)}
    form_3 = {i:[] for i in range(1,5)}
    form_4 = {i:[] for i in range(1,5)}

    fdr = {i:[] for i in range(1,5)}

    form_std = {i:[] for i in range(1,5)}
    form_max = {i:[] for i in range(1,5)}
    form_med = {i:[] for i in range(1,5)}
    
    form_inf = {i:[] for i in range(1,5)}
    score = {i:[] for i in range(1,5)}

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 4:
                continue
                
            fdr[pos].append(3.5-p["fdr"][i])
            form_1[pos].append(np.mean(p["points"][i-1]))            
            form_2[pos].append(np.mean(p["points"][i-2]))            
            form_3[pos].append(np.mean(p["points"][i-3]))            
            form_4[pos].append(np.mean(p["points"][i-4]))       
            form_inf[pos].append(np.mean(p["points"][:i]))      
            form_med[pos].append(np.median(p["points"][:i]))      
            
            #if i >= 10:
            #    form_inf[pos].append(np.mean(p["points"][i-10:i]))   
            #else:
            #    form_inf[pos].append(np.mean(p["points"][:i]))            
            
            form_max[pos].append(np.amax(p["points"][:i]))            
            form_std[pos].append(np.std(p["points"][:i]))            


            score[pos].append(p["points"][i])

    print("")

    fitted_model = {}
    var_names = ["points_1","points_2","points_3","points_4","points_mean","points_med"]#,"fdr"] #"points_1_sqrd","points_2_sqrd","points_inf_sqrd","points_max","points_std","fdr"]

    for i in range(1,5):
                
        print("Position:",i)
        

        y = np.array(score[i])
                
        all_x = []
                
        all_x.append(np.array(form_1[i]))
        all_x.append(np.array(form_2[i]))
        all_x.append(np.array(form_3[i]))
        all_x.append(np.array(form_4[i]))

        all_x.append(np.array(form_inf[i]))
        all_x.append(np.array(form_med[i]))

        #all_x.append(np.array(form_1[i])**2)
        #all_x.append(np.array(form_2[i])**2)       
        #all_x.append(np.array(form_inf[i])**2)

        #all_x.append(np.array(form_max[i]))
        #all_x.append(np.array(form_std[i]))
        #all_x.append(np.array(fdr[i]))


        x = np.array(all_x).T             
        
        #x = sm.add_constant(x)
        mod = sm.OLS(y,x)
        fit = mod.fit()       

        p_values = fit.pvalues

        alpha = 0.05
        worst = []
        coeffs = list(fit.params)
        rsq = fit.rsquared            
        
        
        #while max(p_values) > alpha:  
        #
        #    worst.append(np.argmax(p_values))
        #
        #    new_x = np.array([var for k,var in enumerate(all_x) if k+1 not in worst]).T
        #
        #    #if 0 not in worst:
        #    #    new_x = sm.add_constant(new_x)
        #    mod = sm.OLS(y,new_x)
        #    fit = mod.fit()  
        #    print(fit.summary())
        #
        #    new_p_values = fit.pvalues
        #    rsq = fit.rsquared                
        #    new_coeffs = fit.params
        #
        #    l = 0
        #    for k,v in enumerate(coeffs):
        #        if k in worst:
        #            coeffs[k] = 0.0
        #            p_values[k] = 0.0
        #        else:
        #            coeffs[k] = new_coeffs[l]
        #            p_values[k] = new_p_values[l]
        #            l += 1                                                

        print(rsq,p_values)
        for name,c in zip(var_names,coeffs):
            print(name,c)
        print("")

        fitted_model[i] = coeffs
        
        if plot:
            k = 1
            for m in range(len(all_x)):
                if m+1 in worst:
                    print(f"x{m+1} not part of fit")
                    continue           
                    
                fig = plt.figure(figsize=(12,8))
                fig = sm.graphics.plot_regress_exog(fit, f'x{k}', fig=fig)
                plt.show()        
                k += 1        
            
    
    print("")
    
    if save:
        with open("simple_points_model.txt","w") as f:
            
            f.write("Position;FDR;")
            for name in var_names:
                f.write(name+";")
            f.write("\n")
    
            for i, coeffs in fitted_model.items():
                f.write(str(i)+";-1;")
                for c in coeffs:
                    f.write(str(c)+";")
                f.write("\n")


def create_fdr_points_model(players,save=False):

    form_1 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_2 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_3 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_4 = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    form_std = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    form_max = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    
    form_inf = {j:{i:[] for i in range(1,5)} for j in range(2,6)}
    score = {j:{i:[] for i in range(1,5)} for j in range(2,6)}

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 4:
                continue
                
            fdr = p["fdr"][i]      
            form_1[fdr][pos].append(np.mean(p["points"][i-1]))            
            form_2[fdr][pos].append(np.mean(p["points"][i-2]))            
            form_3[fdr][pos].append(np.mean(p["points"][i-3]))            
            form_4[fdr][pos].append(np.mean(p["points"][i-4]))            
            form_inf[fdr][pos].append(np.mean(p["points"][:i]))            
            
            form_max[fdr][pos].append(np.amax(p["points"][:i]))            
            form_std[fdr][pos].append(np.std(p["points"][:i]))            


            score[fdr][pos].append(p["points"][i])

    print("")

    fitted_model = {}
    var_names = ["points_1","points_2","points_inf","points_1_sqrd","points_2_sqrd","points_inf_sqrd","points_max","points_std"]

    for i in range(1,5):
        
        fitted_model[i] = {}
        
        print("Position:",i)
        
        for j in range(2,6):
            print("FDR:",j)

            y = np.array(score[j][i])
                    
            all_x = []
                    
            all_x.append(np.array(form_1[j][i]))
            all_x.append(np.array(form_2[j][i]))
            all_x.append(np.array(form_inf[j][i]))

            all_x.append(np.array(form_1[j][i])**2)
            all_x.append(np.array(form_2[j][i])**2)       
            all_x.append(np.array(form_inf[j][i])**2)

            all_x.append(np.array(form_max[j][i]))
            all_x.append(np.array(form_std[j][i]))


            x = np.array(all_x).T             
            
            #x = sm.add_constant(x)
            mod = sm.OLS(y,x)
            fit = mod.fit()       

            p_values = fit.pvalues

            alpha = 0.05
            worst = []
            coeffs = list(fit.params)
            rsq = fit.rsquared            
            
            
            #while max(p_values) > alpha:  
            #
            #    worst.append(np.argmax(p_values))
            #
            #    new_x = np.array([var for k,var in enumerate(all_x) if k+1 not in worst]).T
            #
            #    #if 0 not in worst:
            #    #    new_x = sm.add_constant(new_x)
            #    mod = sm.OLS(y,new_x)
            #    fit = mod.fit()  
            #    print(fit.summary())
            #
            #    new_p_values = fit.pvalues
            #    rsq = fit.rsquared                
            #    new_coeffs = fit.params
            #
            #    l = 0
            #    for k,v in enumerate(coeffs):
            #        if k in worst:
            #            coeffs[k] = 0.0
            #            p_values[k] = 0.0
            #        else:
            #            coeffs[k] = new_coeffs[l]
            #            p_values[k] = new_p_values[l]
            #            l += 1                                                

            print(rsq)
            for name,c in zip(var_names,coeffs):
                print(name,c)
            print("")

            fitted_model[i][j] = coeffs
            
            k = 1
            for m in range(len(all_x)):
                if m+1 in worst:
                    print(f"x{m+1} not part of fit")
                    continue           
                    
                fig = plt.figure(figsize=(12,8))
                fig = sm.graphics.plot_regress_exog(fit, f'x{k}', fig=fig)
                plt.show()        
                k += 1        
                
        
        print("")
    
    if save:
        with open("fdr_points_model.txt","w") as f:
            
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

def create_simple_points_model(players,save=False):

    form_1 = {i:[] for i in range(1,5)}
    form_2 = {i:[] for i in range(1,5)}
    form_3 = {i:[] for i in range(1,5)}
    form_4 = {i:[] for i in range(1,5)}
    form_inf = {i:[] for i in range(1,5)}
    
    minutes_1 = {i:[] for i in range(1,5)}
    minutes_2 = {i:[] for i in range(1,5)}
    minutes_3 = {i:[] for i in range(1,5)}
    minutes_4 = {i:[] for i in range(1,5)}    
    minutes_inf = {i:[] for i in range(1,5)} 

    played_last_games = {i:[] for i in range(1,5)} 
    
    score = {i:[] for i in range(1,5)}    

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 4:
                continue
                
            form_1[pos].append(p["points"][i-1])            
            form_2[pos].append(p["points"][i-2])            
            form_3[pos].append(p["points"][i-3])            
            form_4[pos].append(p["points"][i-4])      
            form_inf[pos].append(np.mean(p["points"][:i])) 

            minutes_1[pos].append(p["minutes"][i-1])            
            minutes_2[pos].append(p["minutes"][i-2])            
            #minutes_3[pos].append(p["minutes"][i-3])            
            #minutes_4[pos].append(p["minutes"][i-4])                
            minutes_inf[pos].append(np.mean(p["minutes"][:i]))       
            
            if p["minutes"][i-1] > 60:
                played_last_games[pos].append(1)
            else:
                played_last_games[pos].append(0)
            
            #assists[pos].append(np.mean(p["assists"][:i]))   
            #goals_conceded[pos].append(np.mean(p["goals_conceded"][:i]))   
            #clean_sheets[pos].append(np.mean(p["clean_sheets"][:i]))   
            #goals_scored[pos].append(np.mean(p["goals_scored"][:i]))   
            #is_home[pos].append(p["is_home"][i])
            #if is_home[pos][-1] == 1:
            #    is_away[pos].append(0)
            #else:
            #    is_away[pos].append(1)
            
            score[pos].append(p["points"][i])

    print("")

    fitted_model = {}

    #var_names = ["const"]
    var_names = ["points_1","points_2","points_inf"]#,"points_1_sqrd","points_2_sqrd","points_inf_sqrd"]
    #var_names += ["minutes_1","minutes_inf"]
    #var_names += ["is_home","is_away"]
    #var_names += ["assists"]
    #var_names += ["goals_conceded"]
    #var_names += ["clean_sheets"]
    #var_names += ["goals_scored"]

    for i in range(1,5):
        
        print("Position:",i)

        y = np.array(score[i])
                
        all_x = []
                
        all_x.append(np.array(form_1[i]))
        all_x.append(np.array(form_2[i]))
        all_x.append(np.array(form_inf[i]))

        #all_x.append(np.array(form_1[i])**2)
        #all_x.append(np.array(form_2[i])**2)       
        #all_x.append(np.array(form_inf[i])**2)
        
        #all_x.append(np.array(form_3[i]))
        #all_x.append(np.array(form_4[i]))
        
        #all_x.append(np.array(played_last_games[i]))

        #all_x.append(np.array(minutes_1[i]))
        #all_x.append(np.array(minutes_2[i]))
        #all_x.append(np.array(minutes_3[i]))
        #all_x.append(np.array(minutes_4[i]))         
        #all_x.append(np.array(minutes_inf[i]))
        #
        #all_x.append(np.array(is_home[i]))
        #all_x.append(np.array(is_away[i]))
        #
        #all_x.append(np.array(assists[i]))
        #
        #all_x.append(np.array(goals_conceded[i]))
        #
        #all_x.append(np.array(clean_sheets[i]))
        #
        #if i > 1:
        #    all_x.append(np.array(goals_scored[i]))
                
        x = np.array(all_x).T             
        
        #x = sm.add_constant(x)
        mod = sm.OLS(y,x)
        fit = mod.fit()       

        #print(fit.summary())

        p_values = fit.pvalues

        alpha = 0.05
        worst = []
        coeffs = list(fit.params)         
        rsq = fit.rsquared      

        while max(p_values) > alpha:  
        
            #print("Refitting:",list(p_values))
            worst.append(np.argmax(p_values))
        
            new_x = np.array([var for k,var in enumerate(all_x) if k+1 not in worst]).T
        
            #if 0 not in worst:
            #    new_x = sm.add_constant(new_x)
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
        
        
        #print(var_names,coeffs)
        print(rsq,sum(coeffs[:5]),sum(coeffs[5:])*90)
        for name,c in zip(var_names,coeffs):
            print(name,c)
        print("")

        fitted_model[i] = coeffs
        
        q = 1
        for m in range(len(all_x)):
            if m+1 in worst:
                print(f"x{m+1} not part of fit")
                continue           
                
            fig = plt.figure(figsize=(12,8))
            fig = sm.graphics.plot_regress_exog(fit, f'x{q}', fig=fig)
            plt.show()        
            q += 1        
        
        print("")

    if save:
        with open("simple_points_model.txt","w") as f:
            
            f.write("Position;FDR;")
            for name in var_names:
                f.write(name+";")
            f.write("\n")
            
            for i, coeffs in fitted_model.items():
                f.write(str(i)+";-1;")
                for c in coeffs:
                    f.write(str(c)+";")

                n = len(coeffs)
                while n < len(var_names):
                    f.write("0.0;")
                    n+=1
                    
                f.write("\n")

def create_big_simple_model(players,save=False):

    form_1 = {i:[] for i in range(1,5)}
    form_2 = {i:[] for i in range(1,5)}
    form_3 = {i:[] for i in range(1,5)}
    form_4 = {i:[] for i in range(1,5)}

    minutes_1 = {i:[] for i in range(1,5)}
    minutes_2 = {i:[] for i in range(1,5)}
    minutes_3 = {i:[] for i in range(1,5)}
    minutes_4 = {i:[] for i in range(1,5)}

    assists_1 = {i:[] for i in range(1,5)}
    assists_2 = {i:[] for i in range(1,5)}
    assists_3 = {i:[] for i in range(1,5)}
    assists_4 = {i:[] for i in range(1,5)}

    goals_conceded_1 = {i:[] for i in range(1,5)}
    goals_conceded_2 = {i:[] for i in range(1,5)}
    goals_conceded_3 = {i:[] for i in range(1,5)}
    goals_conceded_4 = {i:[] for i in range(1,5)}

    clean_sheets_1 = {i:[] for i in range(1,5)}
    clean_sheets_2 = {i:[] for i in range(1,5)}
    clean_sheets_3 = {i:[] for i in range(1,5)}
    clean_sheets_4 = {i:[] for i in range(1,5)}

    goals_scored_1 = {i:[] for i in range(1,5)}
    goals_scored_2 = {i:[] for i in range(1,5)}
    goals_scored_3 = {i:[] for i in range(1,5)}
    goals_scored_4 = {i:[] for i in range(1,5)}

    is_home = {i:[] for i in range(1,5)}
    is_away = {i:[] for i in range(1,5)}
    
    score = {i:[] for i in range(1,5)}

    for pid,p in players.items():
        pos = p["position"]
        
        for i,m in enumerate(p["minutes"]):
            if i < 4:
                continue
                
            form_1[pos].append(p["points"][i-1])            
            form_2[pos].append(np.mean(p["points"][:i]))
   

            minutes_1[pos].append(p["minutes"][i-1]) 
            minutes_2[pos].append(np.mean(p["minutes"][:i])) 
            
            assists_1[pos].append(p["assists"][i-1])
            assists_2[pos].append(np.mean(p["assists"][:i]))
            
            goals_conceded_1[pos].append(p["goals_conceded"][i-1])       
            goals_conceded_2[pos].append(np.mean(p["goals_conceded"][:i]))        

            clean_sheets_1[pos].append(p["clean_sheets"][i-1])       
            clean_sheets_2[pos].append(np.mean(p["clean_sheets"][:i]))  
            
            goals_scored_1[pos].append(p["goals_scored"][i-1])       
            goals_scored_2[pos].append(np.mean(p["goals_scored"][:i]))   
            
            is_home[pos].append(p["is_home"][i])
            if is_home[pos][-1] == 0:                
                is_away[pos].append(1)
            else:
                is_away[pos].append(0)

            score[pos].append(p["points"][i])

    print("")

    fitted_model = {}
    var_names = ["const"]#,"points_last","points_average","minutes_last","minutes_average"]
    var_names += [f"points_{i+1}" for i in range(2)]
    var_names += [f"minutes_{i+1}" for i in range(2)]
    var_names += ["is_home","is_away"]
    var_names += [f"assists_{i+1}" for i in range(2)]
    var_names += [f"goals_conceded_{i+1}" for i in range(2)]
    var_names += [f"clean_sheets_{i+1}" for i in range(2)]
    var_names += [f"goals_scored_{i+1}" for i in range(2)]

    for i in range(1,5):
        
        fitted_model[i] = {}
        
        print("Position:",i)        

        y = np.array(score[i])
                
        all_x = []
                
        all_x.append(np.array(form_1[i]))
        all_x.append(np.array(form_2[i]))
         
        all_x.append(np.array(minutes_1[i]))
        all_x.append(np.array(minutes_2[i]))
        
        all_x.append(np.array(is_home[i]))
        all_x.append(np.array(is_away[i]))
        
        all_x.append(np.array(assists_1[i]))
        all_x.append(np.array(assists_2[i]))
        
        all_x.append(np.array(goals_conceded_1[i]))
        all_x.append(np.array(goals_conceded_2[i]))
        
        all_x.append(np.array(clean_sheets_1[i]))
        all_x.append(np.array(clean_sheets_2[i]))
        
        if i > 1:
            all_x.append(np.array(goals_scored_1[i]))
            all_x.append(np.array(goals_scored_2[i]))
        
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
            
        #print(var_names,coeffs)
        print(rsq)
        for name,c in zip(var_names,coeffs):
            print(name,c)
        print("")

        fitted_model[i] = coeffs
        
        #q = 1
        #for m in range(len(all_x)):
        #    if m+1 in worst:
        #        print(f"x{m+1} not part of fit")
        #        continue           
        #        
        #    fig = plt.figure(figsize=(12,8))
        #    fig = sm.graphics.plot_regress_exog(fit, f'x{q}', fig=fig)
        #    plt.show()        
        #    q += 1        
    
    
    
    print("")
    
    if save:
        with open("big_simple_linear_model.txt","w") as f:
            
            f.write("Position;FDR;")
            for name in var_names:
                f.write(name+";")
            f.write("\n")
            
            for i, coeffs in fitted_model.items():
                f.write(str(i)+";-1;")
                for c in coeffs:
                    f.write(str(c)+";")
                    
                n = len(coeffs)
                while n < len(var_names):
                    f.write("0.0;")
                    n+=1
                    
                f.write("\n")




def main():

    seasons = ["2018-19","2019-20","2020-21"]
        
    players = {}
    for i,season in enumerate(seasons):
        print("reading season ",season)
        
        p = get_player_stats(season)

        for k,v in p.items():
            players[k+i*10000] = v

    test_model(players,plot=True,save=False)    

    #create_big_fdr_model(players,save=True)    
    #create_average_fdr_model(players,save=True)

    #create_fdr_points_model(players,save=False)
    #create_simple_points_model(players,save=False)

    #create_average_simple_model(players,save=True)
    #create_big_simple_model(players,save=True)    

if __name__ == "__main__":
    main()