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

class Player(object):
    def __init__(self,name,cost,form,tot_points,minutes,position,team):
        self.name = name
        self.cost = cost
        self.position = position
        self.team = team
        self.form = form
        self.tot_points = tot_points
        self.minutes = minutes
        
        self.score = 0.0        
        self.is_chosen = False
        self.is_cap = False
        self.on_pitch = False
        self.transferred = False
        
    def display(self):
        print(f"Player: {self.name}, {self.team}, {self.position}. Cost {self.cost}, Score {self.score}")

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

    def build_best_formation_model(self,players,existing_players=[],budget = 100.0):
        
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
            
            return cap_score + 0.99*form_score + 0.01*bench_score - 6*m.n_changes
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
      
    def solve_model(self):
        
        model = self.model
        
        self.solver.solve(model,load_solutions=True,tee=False)

        N_chosen = 0
        N_cap = 0 
        
        self.chosen_players = []
        self.captain = None
        self.opt_form = None
        self.opt_j = -1        
        
        self.extra_transfers = self.model.n_changes.value
        self.n_keep = self.model.n_keep.value
                
        try:
            existing_players = model.I_existing            
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
                    player.display()
                
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


