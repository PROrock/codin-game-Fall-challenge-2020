import copy
import timeit
from collections import deque
from operator import add

import sys

MAX_LEVEL = 20
# 40ms in second fraction (hopefully)
TIME_THRES = 40*0.001
TIMEOUT_KEY = -6
MAX_SPELL_SIZE = 17

def debug(text):
    print(text, file=sys.stderr, flush=True)

class Ingr:
    def __init__(self, ingr):
        self.ingr = ingr
    def apply(self, other):
        inventory = list(map(add, other.ingr, self.ingr))
        return Ingr(inventory)
    def is_valid(self):
        return all(i>=0 for i in self.ingr) and sum(self.ingr) <= 10
    def is_applied_valid(self, other):
        s = 0
        for i, j in zip(self.ingr, other.ingr):
            sum_ij = i+j
            if sum_ij < 0:
                return False
            s += sum_ij
        return True

    def __eq__(self, other):
        return self.ingr == other.ingr
    def __hash__(self):
        return hash(tuple(self.ingr))
    def __repr__(self):
        return f"{self.ingr}"


class Action:
    def __init__(self, id, kind, ingr, price, castable, repeatable, tome_index, tax_count):
        self.id = id
        self.kind = kind
        self.ingr = ingr
        self.price = price
        self.castable = castable
        self.repeatable = repeatable
        self.tome_index = tome_index
        self.tax_count = tax_count

    def __repr__(self):
        return (f'{self.__class__.__name__[0]}('
                f'{self.kind} {self.id}, {self.ingr!r}, {self.price})')

    # # todo just approx now - proper search would be better
    # def n_turns(self, score):
    #     n = 0
    #     for i in range(len(self.ingr)):
    #         n += max(score.ingr[i] - self.ingr[i], 0)*(i+1)
    #         print(f"N {i}: diff is {score.ingr[i] - self.ingr[i]}, n is {n}", file=sys.stderr, flush=True)
    #     print(f"N_turns {score} to {self} takes ~ {n} turns", file=sys.stderr, flush=True)
    #     return n

    def to_output(self):
        return "REST" if self.kind == "REST" else f"{self.kind} {self.id}"
    def __eq__(self, other):
        raise NotImplementedError
    def __hash__(self):
        raise NotImplementedError


REST_ACTION = Action(-1, "REST", [0,0,0,0], 0, False, False, -1, 0)

# todo use only Action class - but won't speed up the code I think
class Recipe(Action):
    def __init__(self, id, ingr, price):
        super().__init__(id, "BREW", ingr, price, False, False, -1, 0)


class State:
    def __init__(self, ingr, spells, tome):
        self.ingr = ingr
        self.spells = spells  # non-casted spell ids
        self.tome = tome
    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.ingr!r}, \nspells={self.spells!r})\ntome={self.tome}')
    def __eq__(self, other):
        return self.ingr == other.ingr and self.spells == other.spells and self.tome == other.tome
    def __hash__(self):
        return hash((self.ingr, self.spells, tuple(self.tome)))

class Node:
    def __init__(self, state, f, history):
        self.state = state
        self.f = f
        self.history = history

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.f!r}, {self.state.ingr!r}\n{self.history!r})')

    def satisfies(self, target):
        return self.state.ingr.is_applied_valid(target.ingr)

    def getHistoryWithActionId(self, action_id):
        return copy.copy(self.history) + [action_id] if self.f == 1 else self.history

    def expand(self):
        expanded = []
        new_f = self.f+1
        # recipes - not needed - cannot help me with another recipe
        # spells
        for spell_id in self.state.spells:
            spell = actions[spell_id]
            new_ingr = spell.ingr.apply(self.state.ingr)
            if new_ingr.is_valid():
                copied_spells = self.state.spells - {spell_id}
                expanded.append(Node(State(new_ingr, copied_spells, self.state.tome),
                                     new_f, self.getHistoryWithActionId(spell_id)))
        # learn new spells
        for i, tome_id in enumerate(self.state.tome):
            if i > self.state.ingr.ingr[0]:
                continue # cannot learn, not enough tier-0 ingredients
            new_ingr = Ingr([actions[tome_id].tax_count-i,0,0,0]).apply(self.state.ingr)
            # todo ignoring my adding to tax_count now (I can increase it with my actions)
            # todo: the excess is discarded. manually update new_ingr to max 10

            copied_spells = self.state.spells | {tome_id}
            copied_tome = copy.copy(self.state.tome)
            copied_tome.remove(tome_id)
            expanded.append(Node(State(new_ingr, copied_spells, copied_tome),
                                 new_f, self.getHistoryWithActionId(tome_id)))

        # rest
        if len(self.state.spells) < len(spells):
            copied_spells = frozenset(s.id for s in spells)
            expanded.append(Node(State(self.state.ingr, copied_spells, self.state.tome),
                                 new_f, self.getHistoryWithActionId(REST_ACTION.id)))
        return expanded

def search(state, targets):
    found = {}
    visited = set()
    curr_level = 1
    n_level_nodes = 0
    q = deque([Node(state, 1, [])])

    while len(q) > 0:
        node = q.popleft() ## take first element -> breadth-first
        if node.f > curr_level:
            # debug(f"{curr_level}: {n_level_nodes} processed")
            curr_level = node.f
            n_level_nodes = 0
            # so it ends sometime - just for profiling
            # if node.f > MAX_LEVEL:
            #     debug(f"{node.f} is already MAX_LEVEL. Quitting.")
            #     return found

        n_level_nodes+=1
        if node.state in visited:
            continue

        curr_time=timeit.default_timer()
        if (curr_time-start_time) > TIME_THRES:
            debug(f"Time's up! Current level: {curr_level}")
            found[TIMEOUT_KEY] = TIMEOUT_KEY
            return found

        for target in targets:
            if node.satisfies(target):
                debug(f"Satisfied node: {node}")
                found[target.id] = node
                targets.remove(target)
                if len(targets) == 0:
                    return found
        expanded = node.expand()
        q.extend(expanded) ## put at the end
        visited.add(node.state)
    debug("Cannot find a way to do some recipe :-(")
    return found

def possible_recipe():
    for recipe in recipes:
        new_score = recipe.ingr.apply(my_score)
        if new_score.is_valid():
            return recipe.id
    return None

def valid_spell():
    for spell in spells:
        if not spell.castable:
            continue
        new_score = spell.ingr.apply(my_score)
        if new_score.is_valid():
            return spell.id
    return REST_ACTION.id

# slow, innefficient to run the search from the beginningm when it is the same space to search
# def best():
#     shortest_paths = [Search(State(my_score, recipes, {s.id for s in spells if s.castable}), r).search() for r in recipes]
#     ratios = [r.price/node.f for r, node in zip(recipes, shortest_paths)]
#     return min(enumerate(shortest_paths), key=lambda i:ratios[i]).history[0]
def best():
    tome = [a.id for a in actions.values() if a.kind == "LEARN"]
    tome.sort(key=lambda id:actions[id].tome_index)
    shortest_paths = search(State(Ingr(my_score.ingr), frozenset([s.id for s in spells if s.castable]), tome), recipes)

    if not shortest_paths or TIMEOUT_KEY in shortest_paths.keys():
        if len(spells) < MAX_SPELL_SIZE:
            free_tome = tome[0]
            return free_tome
        else:
            recipe_id = possible_recipe()
            return recipe_id if recipe_id is not None else valid_spell()


    ratios = {r.id:(r.price/shortest_paths[r.id].f) for r in recipes if r.id in shortest_paths.keys()}
    max_id = max((r_id for r_id in ratios.keys()), key=lambda id:ratios[id])
    debug(f"max ratio {ratios[max_id]} has recipe id {max_id}")
    best_node = shortest_paths[max_id]
    action_id = best_node.history[0] if len(best_node.history) > 0 else max_id
    return action_id


# game loop
while True:
    start_time = timeit.default_timer()
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
        # debug(" ".join((action_id, action_type, delta_0, delta_1, delta_2, delta_3, price, tome_index, tax_count, castable, repeatable)))
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
        action = Action(action_id, action_type, ingr, price, castable, repeatable, tome_index, tax_count)
        actions[action_id] = action
        if action_type == 'BREW':
            recipes.append(action)
        elif action_type == 'CAST':
            spells.append(action)

    # for a in actions.values():
    #     debug(a)


    score_line = [int(j) for j in input().split()]
    # debug(score_line)
    my_score = Recipe(-1, score_line[:4], score_line[4])
    score_line = [int(j) for j in input().split()]
    # debug(score_line)
    opp_score = Recipe(-1, score_line[:4], score_line[4])
    # for i in range(2):
    #     # inv_0: tier-0 ingredients in inventory
    #     # score: amount of rupees
    #     inv_0, inv_1, inv_2, inv_3, score = [int(j) for j in input().split()]


    best_action_id = best()
    best_action = actions[best_action_id]
    # debug(f"best action is {best_action}")
    # for a in actions.items():
        # debug(a)
    output = best_action.to_output()

    # in the first league: BREW <id> | WAIT; later: BREW <id> | CAST <id> [<times>] | LEARN <id> | REST | WAIT
    print(output)
