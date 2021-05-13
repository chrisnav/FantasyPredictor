from pyomo.environ import ConcreteModel,Set,RangeSet,Param,Suffix,Reals,NonNegativeReals,NonPositiveReals,Binary,Integers,Objective,minimize,maximize,value,SOSConstraint,Any
from pyomo.core import Constraint,Var,Block,ConstraintList,Expression
from pyomo.opt import SolverFactory,SolverStatus,TerminationCondition
import sys 

class Player(object):
    def __init__(self,name,cost,points,position,team):
        self.name = name
        self.cost = cost
        self.points = points
        self.position = position
        self.team = team
        
        self.is_chosen = False
        self.is_cap = False
    
    def display(self):
        print(f"Player: {self.name}, {self.team}, {self.position}. Cost {self.cost}, points {self.points}")

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
    
    def build_basic_model(self,players,existing_players=[],budget = 100.0):
        
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
        
        def init_points(m,i):
            return self.players[i].points
        model.Points = Param(model.I,initialize=init_points)
        
        model.x = Var(model.I,within=Binary)
        model.y_gkp = Var(model.I_gkp,model.J,within=Binary)
        model.y_def = Var(model.I_def,model.J,within=Binary)
        model.y_mid = Var(model.I_mid,model.J,within=Binary)
        model.y_fwd = Var(model.I_fwd,model.J,within=Binary)
        model.z = Var(model.I,within=Binary)
        
        def cost_constraint(m):
            return sum(m.Cost[i]*m.x[i] for i in m.I) <= budget
        model.MaxCost = Constraint(rule=cost_constraint)
        
        def max_per_team_constraint(m,t):
            return sum(m.x[i] for i in m.I if self.players[i].team == t) <= 3
        model.MaxPerTeam = Constraint(model.T, rule=max_per_team_constraint)

        def req_per_pos(m,p):
            return sum(m.x[i] for i in m.I if self.players[i].position == p) == m.ReqPos[p]
        model.ReqPosConstr = Constraint(model.P, rule=req_per_pos)
        
        def gkp_bounds(m,i,j):
            return m.y_gkp[i,j] <= m.x[i]
        model.gkpBounds = Constraint(model.I_gkp,model.J, rule=gkp_bounds)
        
        def def_bounds(m,i,j):
            return m.y_def[i,j] <= m.x[i]
        model.defBounds = Constraint(model.I_def,model.J, rule=def_bounds)

        def mid_bounds(m,i,j):
            return m.y_mid[i,j] <= m.x[i]
        model.midBounds = Constraint(model.I_mid,model.J, rule=mid_bounds)

        def fwd_bounds(m,i,j):
            return m.y_fwd[i,j] <= m.x[i]
        model.fwdBounds = Constraint(model.I_fwd,model.J, rule=fwd_bounds)    
        
        def pick_gkp(m,j):
            return sum(m.y_gkp[i,j] for i in m.I_gkp) == 1
        model.Pickgkp = Constraint(model.J,rule=pick_gkp)
        
        def pick_def(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.y_def[i,j] for i in m.I_def) == n_def
        model.Pickdef = Constraint(model.J,rule=pick_def) 

        def pick_mid(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.y_mid[i,j] for i in m.I_mid) == n_mid
        model.Pickmid = Constraint(model.J,rule=pick_mid)  

        def pick_fwd(m,j):
            n_def,n_mid,n_fwd = m.Formations[j]
            return sum(m.y_fwd[i,j] for i in m.I_fwd) == n_fwd
        model.Pickfwd = Constraint(model.J,rule=pick_fwd)     
        
        def cap_gkp_bounds(m,i,j):
            return m.z[i] <= m.y_gkp[i,j]
        model.CapgkpBounds = Constraint(model.I_gkp,model.J, rule=cap_gkp_bounds)
        
        def cap_def_bounds(m,i,j):
            return m.z[i] <= m.y_def[i,j]
        model.CapdefBounds = Constraint(model.I_def,model.J, rule=cap_def_bounds)    

        def cap_mid_bounds(m,i,j):
            return m.z[i] <= m.y_mid[i,j]
        model.CapmidBounds = Constraint(model.I_mid,model.J, rule=cap_mid_bounds)   

        def cap_fwd_bounds(m,i,j):
            return m.z[i] <= m.y_fwd[i,j]
        model.CapfwdBounds = Constraint(model.I_fwd,model.J, rule=cap_fwd_bounds)       
        
        def pick_cap(m,j):
            return sum(m.z[i] for i in m.I) == 1
        model.PickCap = Constraint(model.J,rule=pick_cap)
        
        model.n_keep = Var(within=Integers,bounds=(0,14))
        model.n_changes = Var(within=Integers,bounds=(0,14))
        
        if existing_players != []:
        
            model.I_existing = Set(initialize = [i for i,p in enumerate(self.players) if p in existing_players])

            def keep_existing_rule(m):
                return sum(m.x[i] for i in m.I_existing) >= m.n_keep
            model.KeepExisting = Constraint(rule=keep_existing_rule)   

            def changes_rule(m):
                return m.n_changes >= 14 - m.n_keep
            model.CostlyChanges = Constraint(rule = changes_rule)            
            
        else:
            model.n_keep.value = 0
            model.n_keep.fix()            
            model.n_changes.value = 0
            model.n_changes.fix()
        
        def objective_rule(m):
            cap_points = sum(m.Points[i]*m.z[i] for i in model.I)
            gkp_points = sum(m.Points[i]*m.y_gkp[i,j] for i in model.I_gkp for j in model.J)
            def_points = sum(m.Points[i]*m.y_def[i,j] for i in model.I_def for j in model.J)
            mid_points = sum(m.Points[i]*m.y_mid[i,j] for i in model.I_mid for j in model.J)
            fwd_points = sum(m.Points[i]*m.y_fwd[i,j] for i in model.I_fwd for j in model.J)            
            
            return cap_points + (gkp_points+def_points+mid_points+fwd_points)/len(model.J) - 4*m.n_changes
        model.OBJ = Objective(rule=objective_rule,sense=maximize)        

        self.model = model                   
      
    def solve_model(self):
        
        model = self.model
        
        self.solver.solve(model,load_solutions=True,tee=False)

        N_chosen = 0
        N_cap = 0 
        
        self.chosen_players = []
        self.captain = None

        for i in model.I:
            
            #if N_chosen == 15 and N_cap == 1:
            #    break
        
            player = self.players[i]
            
            if model.x[i].value >= 0.9999:
                player.is_chosen = True
                N_chosen += 1
                self.chosen_players.append(player)
            
            if model.z[i].value >= 0.9999:
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
        print("Total points:",sum(p.points for p in self.chosen_players)+self.captain.points)
        print("")
        
        Gkp = [p for p in self.chosen_players if p.position=="gkp"]
        Def = [p for p in self.chosen_players if p.position=="def"]
        Mid = [p for p in self.chosen_players if p.position=="mid"]
        Fwd = [p for p in self.chosen_players if p.position=="fwd"]        
        
        print("Goalkeepers:")
        for p in Gkp:
            print(p.name,p.team,p.cost,p.points)
        print("")

        print("Defenders:")
        for p in Def:
            print(p.name,p.team,p.cost,p.points)    
        print("")

        print("Midfielders:")
        for p in Mid:
            print(p.name,p.team,p.cost,p.points)    
        print("")

        print("Forwards:")
        for p in Fwd:
            print(p.name,p.team,p.cost,p.points)
        print("")

        print("Captain:")
        print(self.captain.name,self.captain.team,self.captain.cost,self.captain.points)
        print("")        


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
        
        if cost == -1:
            l_split = l.split()
            cost = float(l_split[0])
            points = float(l_split[3])
            
            p = Player(name,cost,points,pos,team)
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
        
    players = {}
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
            players[name] = team
            
            name = ""
            team = ""     
            team_short = ""
            
    return players,bank
        
        
        
    
