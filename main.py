import sys
import math
from operator import add
import copy

def debug(text):
    print(text, file=sys.stderr, flush=True)

class Ingr:
    def __init__(self, ingr):
        self.ingr = ingr
    def apply(self, other):
        inventory = list(map(add, other.ingr, self.ingr))
        return Ingr(inventory)
    def is_valid(self):
        return all((i>=0 for i in self.ingr)) and sum(self.ingr) <= 10
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
    def __hash__(self):
        return hash((val for _,val in self.__dict__))
    def __repr__(self):
        return f"{self.ingr}"

    

class Action:
    def __init__(self, id, kind, ingr, price, castable, repeatable):
        self.id = id
        self.kind = kind
        self.ingr = ingr
        self.price = price 
        self.castable = castable
        self.repeatable = repeatable

    # def apply(self, score):
        # inventory = list(map(add, score.ingr, self.ingr) )
        # return Action(-1, None, inventory, score.price + self.price, False, False)

    # def is_valid(self):
        # return all((i>=0 for i in self.ingr)) and sum(self.ingr) <= 10

    def __repr__(self):
        return (f'{self.__class__.__name__[0]}('
                f'{self.kind} {self.id!r}, {self.ingr!r}, {self.price!r})')

    # todo just approx now - proper search would be better
    def n_turns(self, score):
        n = 0
        for i in range(len(self.ingr)):
            n += max(score.ingr[i] - self.ingr[i], 0)*(i+1)
            print(f"N {i}: diff is {score.ingr[i] - self.ingr[i]}, n is {n}", file=sys.stderr, flush=True)
        print(f"N_turns {score} to {self} takes ~ {n} turns", file=sys.stderr, flush=True)
        return n

    def to_output(self):
        return "REST" if self.kind == "REST" else f"{self.kind} {self.id}"
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
    def __hash__(self):
        return hash((val for _,val in self.__dict__))


REST_ACTION = Action(-1, "REST", [0,0,0,0], 0, False, False)

class Recipe(Action):
    def __init__(self, id, ingr, price):
        super().__init__(id, "BREW", ingr, price, False, False)

class Spell(Action):
    def __init__(self, id, kind, ingr, price, castable, repeatable):
        super().__init__(id, kind, ingr, price, castable, repeatable)
        self.castable = castable 
        self.repeatable = repeatable
    # def __repr__(self):
        # return f"{super().__repr__()}, cast={self.castable}"


class State:
    def __init__(self, ingr, spells):
        self.ingr = ingr
        # self.recipes = recipes
        self.spells = spells # non-casted spell ids
    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.ingr!r}, \nspells={self.spells!r})')
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)
    def __hash__(self):
        return hash((val for _,val in self.__dict__))

class Node:
    def __init__(self, state, f, history):
        self.state = state
        self.f = f
        self.history = history

    def __repr__(self):
        # {self.state!r}, 
        return (f'{self.__class__.__name__}('
                f'{self.f!r}, {self.state.ingr!r}\n{self.history!r})')

    def satisfies(self, target):
        new_ingr = self.state.ingr.apply(target.ingr)
        return new_ingr.is_valid()

    def expand(self):
        expanded = []
        # recipes - not needed - cannot help me with another recipe
        # spells
        for i, spell_id in enumerate(self.state.spells):
            spell = actions[spell_id]
            new_ingr = spell.ingr.apply(self.state.ingr)
            # print(f"New ingr {new_ingr}", file=sys.stderr, flush=True)
            if new_ingr.is_valid():
                copied_spells = copy.copy(self.state.spells)
                copied_spells.remove(spell_id) 
                # debug(copied_spells[i])
                expanded.append(Node(State(new_ingr, copied_spells), self.f+1, 
                                     copy.copy(self.history) + [spell_id]))
        
        # rest
        if len(self.state.spells) < len(spells):
            copied_spells = [s.id for s in spells]
            expanded.append(Node(State(self.state.ingr, copied_spells), self.f+1, 
                                 copy.copy(self.history) + [-1]))
        # debug(f"Expanded {self}")
        # debug(f"Expanded {self} to {expanded}")
        # debug(self.f)
        return expanded

# seed=-4572190914680882200
class Search:
    def __init__(self, state, targets):
        self.state = state
        self.targets = targets

    def search(self):
        found = {}
        visited = set()
        curr_level = 0
        n_level_nodes = 0
        q = [Node(self.state, 0, [])]
        while len(q) > 0:
            node = q.pop(0) ## take first element -> breadth-first
            n_level_nodes+=1
            if node.state in visited:
                # debug(f"Already visited state {node.state}")
                continue
            for target in self.targets:
                if node.satisfies(target) and target.id not in found.keys():
                    debug(f"Satisfied node: {node}")
                    found[target.id] = node
                    if len(found) == len(self.targets):
                        return found
            expanded = node.expand()
            q.extend(expanded) ## put at the end
            visited.add(node.state)

            if node.f > curr_level:
                curr_level = node.f
                debug(f"{curr_level}: {n_level_nodes} processed")
        return None


# slow, innefficient to run the search from the beginningm when it is the same space to search
# def best():
#     shortest_paths = [Search(State(my_score, recipes, {s.id for s in spells if s.castable}), r).search() for r in recipes]
#     ratios = [r.price/node.f for r, node in zip(recipes, shortest_paths)]
#     return min(enumerate(shortest_paths), key=lambda i:ratios[i]).history[0]
def best():
    shortest_paths = Search(State(Ingr(my_score.ingr), {s.id for s in spells if s.castable}), recipes).search()
    ratios = {r.id:(r.price/shortest_paths[r.id].f) for r in recipes}
    max_id = max((r.id for r in recipes), key=lambda id:ratios[id])
    debug(f"max ratio {ratios[max_id]} has recipe id {max_id}")
    action_id = shortest_paths[max_id].history[0]
    debug(f"Action id is {action_id}")
    return actions[action_id]


# game loop
while True:
    recipes = []
    spells = []
    tome_spells = []
    actions = {REST_ACTION.id:REST_ACTION}

    action_count = int(input())  # the number of spells and recipes in play
    for i in range(action_count):
        # action_id: the unique ID of this spell or recipe
        # action_type: in the first league: BREW; later: CAST, OPPONENT_CAST, LEARN, BREW
        # delta_0: tier-0 ingredient change
        # delta_1: tier-1 ingredient change
        # delta_2: tier-2 ingredient change
        # delta_3: tier-3 ingredient change
        # price: the price in rupees if this is a potion
        # tome_index: in the first two leagues: always 0; later: the index in the tome if this is a tome spell, equal to the read-ahead tax
        # tax_count: in the first two leagues: always 0; later: the amount of taxed tier-0 ingredients you gain from learning this spell
        # castable: in the first league: always 0; later: 1 if this is a castable player spell
        # repeatable: for the first two leagues: always 0; later: 1 if this is a repeatable player spell
        action_id, action_type, delta_0, delta_1, delta_2, delta_3, price, tome_index, tax_count, castable, repeatable = input().split()
        action_id = int(action_id)
        delta_0 = int(delta_0)
        delta_1 = int(delta_1)
        delta_2 = int(delta_2)
        delta_3 = int(delta_3)
        # todo - just lazy approximation now
        urgency_bonus = 1 if i == 0 else 0
        price = int(price) + urgency_bonus
        tome_index = int(tome_index)
        tax_count = int(tax_count)
        castable = castable != "0"
        repeatable = repeatable != "0"

        ingr = Ingr([delta_0,delta_1,delta_2,delta_3])
        actions[action_id] = Action(action_id, action_type, ingr, price, castable, repeatable)
        if action_type == 'BREW':
            recipes.append(Recipe(action_id, ingr, price))
        elif action_type == 'CAST':
            spells.append(Spell(action_id, action_type, ingr, price, castable, repeatable))
        # elif action_type == 'LEARN':
            # tome_spells.append(Spell(action_id, action_type, ingr, price, castable))

    # for r in recipes:
        # print(r, file=sys.stderr, flush=True)


    score_line = [int(j) for j in input().split()]
    my_score = Recipe(-1, score_line[:4], score_line[4])
    score_line = [int(j) for j in input().split()]
    opp_score = Recipe(-1, score_line[:4], score_line[4])
    # for i in range(2):
    #     # inv_0: tier-0 ingredients in inventory
    #     # score: amount of rupees
    #     inv_0, inv_1, inv_2, inv_3, score = [int(j) for j in input().split()]


    best_action = best()
    # debug(f"best action is {best_action}")
    # for a in actions.items():
        # debug(a)
    output = best_action.to_output()

    # in the first league: BREW <id> | WAIT; later: BREW <id> | CAST <id> [<times>] | LEARN <id> | REST | WAIT
    print(output)
