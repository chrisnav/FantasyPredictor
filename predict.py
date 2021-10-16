from pyomo.environ import ConcreteModel,Set,RangeSet,Param,Suffix,Reals,NonNegativeReals,NonPositiveReals,Binary,Integers,Objective,minimize,maximize,value,SOSConstraint,Any
from pyomo.core import Constraint,Var,Block,ConstraintList,Expression
from pyomo.opt import SolverFactory,SolverStatus,TerminationCondition
import sys 
import os
os.system("color")

COLOR = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
}

class FantasyOptimizer():
    
    def __init__(self, cplex_path):
        
        self.chosen_players = []
        self.captain = None
        
        self.solver = self.init_solver(cplex_path)
    
        self.model = None 
      
    def init_solver(self,cplex_path):
    
        solver = SolverFactory("cplex",executable=cplex_path)
        solver.options["mip tolerances absmipgap"] = 0
        solver.options["mip tolerances mipgap"] = 0    
        
        return solver

    def build_best_formation_model(self,players,budget = 100.0,bench_boost=False):
        
        self.players = players

        model = ConcreteModel()
                
        model.I = RangeSet(0,len(self.players)-1)    
        model.I_gkp = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="gkp"])
        model.I_def = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="def"])
        model.I_mid = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="mid"])
        model.I_fwd = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="fwd"])
        model.J = RangeSet(0,7)

        model.T = Set(initialize=list(set([p.team for p in self.players])))
        model.P = Set(initialize=list(set([p.position for p in self.players])))
        
        def init_formations(m,j):
            if j == 0:
                return (3,5,2)
            if j == 1:
                return (3,4,3)
            if j == 2:
                return (4,5,1)
            if j == 3:
                return (4,4,2)
            if j == 4:
                return (4,3,3)
            if j == 5:
                return (5,4,1)
            if j == 6:
                return (5,3,2)
            if j == 7:
                return (5,2,3)            
        model.Formations = Param(model.J,initialize =init_formations,within=Any)
        
        def init_req_per_pos(m,p):
            if p == "gkp":
                return 2
            if p == "fwd":
                return 3
            return 5
        model.ReqPos = Param(model.P,initialize=init_req_per_pos)
        
        def init_cost(m,i):
            return self.players[i].cost
        model.Cost = Param(model.I,initialize=init_cost)
        
        def init_score(m,i):
            return self.players[i].score
        model.Score = Param(model.I,initialize=init_score)
        
        
        model.in_squad = Var(model.I,within=Binary)               #Players in squad (15)
        model.on_pitch = Var(model.I,model.J,within=Binary)       #Players on the pitch in formation j
        model.cap = Var(model.I,within=Binary)                    #Captain
        model.form_points = Var(model.J, within=Reals)            #Points in formation j
        model.best_form = Var(model.J, within=Binary)             #The best formation to use (max points)
        model.n_keep = Var(within=Integers,bounds=(0,15))         #The number of players kept from the existing team (if given)
        model.n_changes = Var(within=Integers,bounds=(0,15))      #The number of changes from the existing team (if given)
        
        def cost_constraint(m):
            return sum(m.Cost[i]*m.in_squad[i] for i in m.I) <= budget
        model.MaxCost = Constraint(rule=cost_constraint)
        
        def max_per_team_constraint(m,t):
            return sum(m.in_squad[i] for i in m.I if self.players[i].team == t) <= 3
        model.MaxPerTeam = Constraint(model.T, rule=max_per_team_constraint)

        def req_per_pos(m,p):
            return sum(m.in_squad[i] for i in m.I if self.players[i].position == p) == m.ReqPos[p]
        model.ReqPosConstr = Constraint(model.P, rule=req_per_pos)
        
        def y_bounds(m,i,j):
            return m.on_pitch[i,j] <= m.in_squad[i]
        model.gkpBounds = Constraint(model.I,model.J, rule=y_bounds)
        
        def pick_gkp(m,j):
            return sum(m.on_pitch[i,j] for i in m.I_gkp) == 1
        model.Pickgkp = Constraint(model.J,rule=pick_gkp)
        
        def pick_def(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j] for i in m.I_def) == n_def
        model.Pickdef = Constraint(model.J,rule=pick_def) 

        def pick_mid(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j] for i in m.I_mid) == n_mid
        model.Pickmid = Constraint(model.J,rule=pick_mid)  

        def pick_fwd(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j] for i in m.I_fwd) == n_fwd
        model.Pickfwd = Constraint(model.J,rule=pick_fwd)     
        
        def cap_bounds(m,i,j):
            return m.cap[i] <= m.on_pitch[i,j]
        model.CapBounds = Constraint(model.I,model.J, rule=cap_bounds)

        def pick_cap(m):
            return sum(m.cap[i] for i in m.I) == 1
        model.PickCap = Constraint(rule=pick_cap)
        
        def pick_formation(m):
            return sum(m.best_form[j] for j in m.J) == 1
        model.PickFormation = Constraint(rule=pick_formation)
        
        def form_point_bound(m,j):
            return m.form_points[j] <= sum(m.Score[i]*m.on_pitch[i,j] for i in model.I)
        model.FormationPointBound = Constraint(model.J, rule=form_point_bound)
        
        def form_pick_bound(m,j):
            big_m = 15*max([p.score for p in self.players])
            return m.form_points[j] <= big_m*m.best_form[j]
        model.FormationPickBounds = Constraint(model.J, rule=form_pick_bound)

        def objective_rule(m):
            cap_score = sum(m.Score[i]*m.cap[i] for i in model.I)
            form_score = sum(m.form_points[j] for j in model.J)       
            bench_score = sum(m.Score[i]*(m.in_squad[i]-m.on_pitch[i,j]) for i in model.I for j in model.J)/len(model.J)
            #smoothing_score = 0.05*sum(m.Score[i]*m.in_squad[i] for i in model.I)/15
            
            if bench_boost:
                return cap_score + form_score + bench_score - 4*m.n_changes
            else:            
                return cap_score + 0.99*form_score + 0.01*bench_score - 4*m.n_changes
        model.OBJ = Objective(rule=objective_rule,sense=maximize)        

        self.model = model          
      
    def add_existing_team(self, existing_team,n_free_transf=1,n_max_transf=15):
        
        model = self.model
        
        model.I_existing = Set(initialize = [i for i,p in enumerate(self.players) if p in existing_team])

        def keep_existing_rule(m):
            return sum(m.in_squad[i] for i in m.I_existing) >= m.n_keep
        model.KeepExisting = Constraint(rule=keep_existing_rule)   

        def changes_rule(m):
            return m.n_changes >= 15 - n_free_transf - m.n_keep
        model.CostlyChanges = Constraint(rule = changes_rule)  

        def max_changes_rule(m):
            return m.n_changes <= n_max_transf - n_free_transf
        model.MaxChanges = Constraint(rule = max_changes_rule)          

    def add_min_team_players(self,team,n):
        
        if n > 3:
            print("Max 3 players from a team is allowed! The input:",team,n)
            return
        
        model = self.model
        
        def min_from_team(m):
            return sum(m.in_squad[i] for i in m.I if self.players[i].team == team) >= n
        model.MinFromTeam = Constraint(rule=min_from_team)
        
    def required_players(self, required_players):

        model = self.model
        
        index = [i for i,p in enumerate(self.players) if p in required_players]

        for i in index:
            model.in_squad[i].value = 1.0
            model.in_squad[i].fix()
            
            for j in model.J:
                model.on_pitch[i,j].value=1.0
                model.on_pitch[i,j].fix()
            
        
        
      
    def solve_model(self):
        
        model = self.model
        
        self.solver.solve(model,load_solutions=True,tee=False)

        N_chosen = 0
        N_cap = 0 
        
        self.chosen_players = []
        self.transferred_out = []
        self.captain = None
        self.opt_form = None
        self.opt_j = -1        
        
        self.extra_transfers = self.model.n_changes.value
        self.n_keep = self.model.n_keep.value
                
        try:
            existing_players = model.I_existing   
            for i in existing_players:
                if model.in_squad[i].value < 0.999:
                    self.transferred_out.append(self.players[i])            
        except:
            existing_players = []

        for j in model.J:
            if model.best_form[j].value >= 0.999:
                
                if self.opt_form is not None:
                    print("Ooops, multiple formations chosen!",j,model.best_form[j].value)
            
                self.opt_form = model.Formations[j]
                opt_j = j
                
        self.opt_form_score = model.form_points[opt_j].value
                
        for i in model.I:
        
            player = self.players[i]
            
            if model.in_squad[i].value >= 0.999:
                player.is_chosen = True
                N_chosen += 1
                self.chosen_players.append(player)
                
                if i not in existing_players:
                    player.transferred = True
                
                if model.on_pitch[i,opt_j].value >= 0.999:
                    player.on_pitch = True
                            
            if model.cap[i].value >= 0.999:
                player.is_cap = True       
                N_cap += 1
                self.captain = player
                
        if N_cap != 1 or N_chosen != 15:
            print(f"OOPS, {N_chosen} players chosen with {N_cap} captains selected!")
             
    def display_results(self):
        
        if len(self.chosen_players) != 15 or self.captain is None:
            print(f"Full team not selected, number of players: {len(self.chosen_players)}, cptain: {self.captain}")
            return            
        
        print("Total cost:",sum(p.cost for p in self.chosen_players))
        print("Total predicted score:",self.opt_form_score+self.captain.score-4*self.extra_transfers)
        print("Total extra transfers, players kept:",self.extra_transfers,self.n_keep)
        print("")
        
        Gkp = [p for p in self.chosen_players if p.position=="gkp"]
        Def = [p for p in self.chosen_players if p.position=="def"]
        Mid = [p for p in self.chosen_players if p.position=="mid"]
        Fwd = [p for p in self.chosen_players if p.position=="fwd"]        
        
        print("Goalkeepers:")
        for p in Gkp:
        
            info = f"{p.name} {p.team} {p.cost} {p.score}"
            
            if p.transferred:
                info = COLOR["RED"]+info+COLOR["ENDC"]
            if not p.on_pitch:
                info = "\t"+info
            
            print(info)
        print("")

        print("Defenders:")
        for p in Def:
            info = f"{p.name} {p.team} {p.cost} {p.score}"
            
            if p.transferred:
                info = COLOR["RED"]+info+COLOR["ENDC"]
            if not p.on_pitch:
                info = "\t"+info
            
            print(info)
        print("")

        print("Midfielders:")
        for p in Mid:
            info = f"{p.name} {p.team} {p.cost} {p.score}"
            
            if p.transferred:
                info = COLOR["RED"]+info+COLOR["ENDC"]
            if not p.on_pitch:
                info = "\t"+info
            
            print(info)
        print("")

        print("Forwards:")
        for p in Fwd:
            info = f"{p.name} {p.team} {p.cost} {p.score}"
            
            if p.transferred:
                info = COLOR["RED"]+info+COLOR["ENDC"]
            if not p.on_pitch:
                info = "\t"+info
            
            print(info)
        print("")

        print("Captain:")
        print(self.captain.name,self.captain.team,self.captain.cost,self.captain.score)
        print("")        
    
        if len(self.transferred_out) > 0:

            print("Players transferred out:")
            for p in self.transferred_out:
                p.display()

    


class MultiWeekFantasyOptimizer():
    
    def __init__(self, cplex_path):
        
        self.chosen_players = []
        self.captain = None
        
        self.solver = self.init_solver(cplex_path)
    
        self.model = None 
      
    def init_solver(self,cplex_path):
    
        solver = SolverFactory("cplex",executable=cplex_path)
        solver.options["mip tolerances absmipgap"] = 0
        solver.options["mip tolerances mipgap"] = 0    
        
        return solver

    def build_best_formation_model(self,players, n_weeks, budget,existing_team,n_free_transf,n_max_transf=15):
        
        self.players = players
        
        model = ConcreteModel()
                
        model.W = RangeSet(0,n_weeks-1)                                                        #Time index
        model.I = RangeSet(0,len(self.players)-1)                                                   #Player index
        model.I_gkp = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="gkp"])   #Goalkeeper index
        model.I_def = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="def"])   #Defender index
        model.I_mid = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="mid"])   #Midfielder index
        model.I_fwd = Set(initialize=[i for i,p in enumerate(self.players) if p.position=="fwd"])   #Forward index
        model.J = RangeSet(0,7)                                                                     #Formation index            
        model.T = Set(initialize=list(set([p.team for p in self.players])))                         #Team index        
        model.P = Set(initialize=list(set([p.position for p in self.players])))                     #Position index
        
        def init_formations(m,j):
            if j == 0:
                return (3,5,2)
            if j == 1:
                return (3,4,3)
            if j == 2:
                return (4,5,1)
            if j == 3:
                return (4,4,2)
            if j == 4:
                return (4,3,3)
            if j == 5:
                return (5,4,1)
            if j == 6:
                return (5,3,2)
            if j == 7:
                return (5,2,3)            
        model.Formations = Param(model.J,initialize =init_formations,within=Any)
        
        def init_req_per_pos(m,p):
            if p == "gkp":
                return 2
            if p == "fwd":
                return 3
            return 5
        model.ReqPos = Param(model.P,initialize=init_req_per_pos)
        
        def init_cost(m,i):
            return self.players[i].cost
        model.Cost = Param(model.I,initialize=init_cost)
        
        def init_score(m,i,w):
            return self.players[i].score[w]
        model.Score = Param(model.I,model.W,initialize=init_score)
        
        def init_existing_team(m,i):
            p = self.players[i]
            if p in existing_team:
                return 1            
            return 0
        model.ExistingTeam = Param(model.I,initialize=init_existing_team)
            
        model.in_squad = Var(model.I,model.W,within=Binary)               #Players in squad (15)
        model.on_pitch = Var(model.I,model.J,model.W,within=Binary)       #Players on the pitch in formation j
        model.cap = Var(model.I,model.W,within=Binary)                    #Captain
        model.form_points = Var(model.J,model.W, within=Reals)            #Points in formation j
        model.best_form = Var(model.J,model.W, within=Binary)             #The best formation to use (max points)
        model.n_changes = Var(model.W,bounds=(0,n_max_transf))            #The number of changes from the previous team
        model.n_free = Var(model.W,bounds=(0,15))                         #The number of free changes this round
        model.n_costly = Var(model.W,bounds=(0,15))                       #The number of costly changes this round
        model.u = Var(model.W,within=Binary)                              #1 if more than 1 change is made this round, 0 otherwise
        model.subbed_in = Var(model.I,model.W,bounds=(0,1))               #Player subbed into team
        model.subbed_out = Var(model.I,model.W,bounds=(0,1))              #Player subbed out of team
        
        
        def cost_constraint(m,w):
            return sum(m.Cost[i]*m.in_squad[i,w] for i in m.I) <= budget
        model.MaxCost = Constraint(model.W,rule=cost_constraint)
        
        def max_per_team_constraint(m,t,w):
            return sum(m.in_squad[i,w] for i in m.I if self.players[i].team == t) <= 3
        model.MaxPerTeam = Constraint(model.T,model.W, rule=max_per_team_constraint)

        def req_per_pos(m,p,w):
            return sum(m.in_squad[i,w] for i in m.I if self.players[i].position == p) == m.ReqPos[p]
        model.ReqPosConstr = Constraint(model.P,model.W, rule=req_per_pos)
        
        def on_pitch_bounds(m,i,j,w):
            return m.on_pitch[i,j,w] <= m.in_squad[i,w]
        model.OnPitchBounds = Constraint(model.I,model.J,model.W, rule=on_pitch_bounds)
        
        def pick_gkp(m,j,w):
            return sum(m.on_pitch[i,j,w] for i in m.I_gkp) == 1
        model.Pickgkp = Constraint(model.J,model.W, rule=pick_gkp)
        
        def pick_def(m,j,w):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j,w] for i in m.I_def) == n_def
        model.Pickdef = Constraint(model.J,model.W, rule=pick_def) 

        def pick_mid(m,j,w):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j,w] for i in m.I_mid) == n_mid
        model.Pickmid = Constraint(model.J,model.W, rule=pick_mid)  

        def pick_fwd(m,j,w):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.on_pitch[i,j,w] for i in m.I_fwd) == n_fwd
        model.Pickfwd = Constraint(model.J,model.W, rule=pick_fwd)     
        
        def cap_bounds(m,i,j,w):
            return m.cap[i,w] <= m.on_pitch[i,j,w]
        model.CapBounds = Constraint(model.I,model.J,model.W, rule=cap_bounds)

        def pick_cap(m,w):
            return sum(m.cap[i,w] for i in m.I) == 1
        model.PickCap = Constraint(model.W,rule=pick_cap)
        
        def pick_formation(m,w):
            return sum(m.best_form[j,w] for j in m.J) == 1
        model.PickFormation = Constraint(model.W,rule=pick_formation)
        
        def form_point_bound(m,j,w):
            return m.form_points[j,w] <= sum(m.Score[i,w]*m.on_pitch[i,j,w] for i in model.I)
        model.FormationPointBound = Constraint(model.J,model.W, rule=form_point_bound)
        
        def form_pick_bound(m,j,w):
            big_m = 15*max([p.score[w] for p in self.players])
            return m.form_points[j,w] <= big_m*m.best_form[j,w]
        model.FormationPickBounds = Constraint(model.J,model.W, rule=form_pick_bound)
        
        def sub_rule(m,i,w):
            if w == 0:
                prev_selection = m.ExistingTeam[i]
            else:
                prev_selection = m.in_squad[i,w-1]
                                
            return m.subbed_in[i,w] - m.subbed_out[i,w] == m.in_squad[i,w] - prev_selection
        model.SubRule = Constraint(model.I,model.W,rule=sub_rule)       

        def total_changes_rule(m,w):
            return m.n_changes[w] == sum(m.subbed_in[i,w] for i in m.I)
        model.TotalChanges = Constraint(model.W, rule=total_changes_rule)

        def costly_changes_rule(m,w):
            return m.n_costly[w] >= m.n_changes[w] - m.n_free[w]
        model.CostlyChanges = Constraint(model.W, rule=costly_changes_rule)
                
        def free_changes_rule(m,w):
            if w == 0:
                return m.n_free[w] == n_free_transf
                
            return m.n_free[w] == 2 - m.u[w]
        model.FreeChanges = Constraint(model.W, rule=free_changes_rule)        

        def remove_free_change_rule(m,w):
            if w == 0:
                return m.u[w] == 0
                
            return 15*m.u[w] >= m.n_changes[w-1] #- 1
        model.RemoveFreeChange = Constraint(model.W, rule=remove_free_change_rule)
        

        
        def objective_rule(m):
            cap_score = sum(m.Score[i,w]*m.cap[i,w] for i in m.I for w in m.W)
            form_score = sum(m.form_points[j,w] for j in m.J for w in m.W)       
            bench_score = sum(m.Score[i,w]*(m.in_squad[i,w]-m.on_pitch[i,j,w]) for i in m.I for j in m.J for w in m.W)/len(m.J)
            #smoothing_score = 0.05*sum(m.Score[i]*m.in_squad[i] for i in m.I)/15
                   
            return cap_score + 0.99*form_score + 0.01*bench_score - 4*sum(m.n_costly[w] for w in m.W)
        model.OBJ = Objective(rule=objective_rule,sense=maximize)        

        self.model = model          


    def add_min_team_players(self,team,n):
        
        if n > 3:
            print("Max 3 players from a team is allowed! The input:",team,n)
            return
        
        model = self.model
        
        def min_from_team(m,w):
            return sum(m.in_squad[i,w] for i in m.I if self.players[i].team == team) >= n
        model.MinFromTeam = Constraint(model.W, rule=min_from_team)
        
    def required_players(self, required_players):

        model = self.model
        
        index = [i for i,p in enumerate(self.players) if p in required_players]

        for w in model.W:
            for i in index:
                model.in_squad[i,w].value = 1.0
                model.in_squad[i,w].fix()
                
                for j in model.J:
                    model.on_pitch[i,j,w].value=1.0
                    model.on_pitch[i,j,w].fix()
                
        
        
      
    def solve_model(self):
        
        model = self.model
        
        self.solver.solve(model,load_solutions=True,tee=False)
             
    def display_results(self):
        
        model = self.model
               
        for w in model.W:

            chosen_players = [] 
            players_on_pitch = [] 
            transferred_in = []
            transferred_out = [] 
            captain = None
            opt_form = None
            opt_j = -1       
            opt_form_score = None
                
            total_transfers = model.n_changes[w].value
            costly_transfers = model.n_costly[w].value        
            
            for j in model.J:
                if model.best_form[j,w].value >= 0.999:
                    
                    if opt_form is not None:
                        print("Ooops, multiple formations chosen!",j,w,model.best_form[j,w].value)
                
                    opt_form = model.Formations[j]
                    opt_j = j
                    
            opt_form_score = model.form_points[opt_j,w].value
                    
            for i in model.I:
            
                player = self.players[i]
                
                if model.in_squad[i,w].value >= 0.999:
                
                    chosen_players.append(player)
                    
                    if model.on_pitch[i,opt_j,w].value >= 0.999:
                        players_on_pitch.append(player)
                                
                    if model.cap[i,w].value >= 0.999:
                        if captain is not None:
                            print("Ooops, multiple captains chosen!",i,w,player.name)

                        captain = player
                    
                    if model.subbed_in[i,w].value >= 0.999:
                        transferred_in.append(player)
                    
                    
                elif model.subbed_out[i,w].value >= 0.999:
                    transferred_out.append(player)
                
                    
            if captain is None or len(chosen_players) != 15 or len(players_on_pitch) != 11:
                print(f"OOPS, {len(chosen_players)} players chosen with {len(players_on_pitch)} on the pitch and {captain} captains selected in week {w}!")        
        
            print("Week:",w)
            print("Total cost:",sum(p.cost for p in chosen_players))
            print("Total predicted score:",opt_form_score + captain.score[w] - 4*costly_transfers)
            print("Total transfers, costly transfers",total_transfers,costly_transfers)
            print("")
            
            Gkp = [p for p in chosen_players if p.position=="gkp"]
            Def = [p for p in chosen_players if p.position=="def"]
            Mid = [p for p in chosen_players if p.position=="mid"]
            Fwd = [p for p in chosen_players if p.position=="fwd"]        
            
            print("Goalkeepers:")
            for p in Gkp:
            
                info = f"{p.name} {p.team} {p.cost} {p.score[w]}"
                
                if p in transferred_in:
                    info = COLOR["RED"]+info+COLOR["ENDC"]
                if p not in players_on_pitch:
                    info = "\t"+info
                
                print(info)
            print("")

            print("Defenders:")
            for p in Def:
                info = f"{p.name} {p.team} {p.cost} {p.score[w]}"
                
                if p in transferred_in:
                    info = COLOR["RED"]+info+COLOR["ENDC"]
                if p not in players_on_pitch:
                    info = "\t"+info
                
                print(info)
            print("")

            print("Midfielders:")
            for p in Mid:
                info = f"{p.name} {p.team} {p.cost} {p.score[w]}"
                
                if p in transferred_in:
                    info = COLOR["RED"]+info+COLOR["ENDC"]
                if p not in players_on_pitch:
                    info = "\t"+info
                
                print(info)
            print("")

            print("Forwards:")
            for p in Fwd:
                info = f"{p.name} {p.team} {p.cost} {p.score[w]}"
                
                if p in transferred_in:
                    info = COLOR["RED"]+info+COLOR["ENDC"]
                if p not in players_on_pitch:
                    info = "\t"+info
                
                print(info)
            print("")

            print("Captain:")
            print(captain.name,captain.team,captain.cost,captain.score[w])
            print("")        
        
            if len(transferred_out) > 0:

                print("Players transferred out:")
                for p in transferred_out:
                    p.display()
                    
            print("\n")
    

