
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
        return self.__dict__ == other.__dict__
    def __hash__(self):
        return hash((val for _,val in self.__dict__))
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

    # def apply(self, score):
    # inventory = list(map(add, score.ingr, self.ingr) )
    # return Action(-1, None, inventory, score.price + self.price, False, False)

    # def is_valid(self):
    # return all((i>=0 for i in self.ingr)) and sum(self.ingr) <= 10

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
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)
    def __hash__(self):
        return hash((val for _,val in self.__dict__))


REST_ACTION = Action(-1, "REST", [0,0,0,0], 0, False, False, -1, 0)

# todo use only Action class - but won't speed up the code I think
class Recipe(Action):
    def __init__(self, id, ingr, price):
        super().__init__(id, "BREW", ingr, price, False, False, -1, 0)

class Spell(Action):
    def __init__(self, id, kind, ingr, price, castable, repeatable):
        super().__init__(id, kind, ingr, price, castable, repeatable, -1, 0)
        self.castable = castable
        self.repeatable = repeatable
    # def __repr__(self):
    # return f"{super().__repr__()}, cast={self.castable}"


class State:
    def __init__(self, ingr, spells, tome):
        self.ingr = ingr
        # self.recipes = recipes
        self.spells = spells  # non-casted spell ids
        self.tome = tome
    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.ingr!r}, \nspells={self.spells!r})\ntome={self.tome}')
    def __eq__(self, other):
        return self.ingr == other.ingr and self.spells == other.spells and self.tome == other.tome
        # return self.__dict__ == other.__dict__
    def __hash__(self):
        return hash(self.ingr, self.spells, self.tome)

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
        for spell_id in self.state.spells:
            spell = actions[spell_id]
            new_ingr = spell.ingr.apply(self.state.ingr)
            # print(f"New ingr {new_ingr}", file=sys.stderr, flush=True)
            if new_ingr.is_valid():
                copied_spells = copy.copy(self.state.spells)
                copied_spells.remove(spell_id)
                # debug(copied_spells[i])
                expanded.append(Node(State(new_ingr, copied_spells, self.state.tome),
                                     self.f+1, copy.copy(self.history) + [spell_id]))
        # learn new spells
        for i, tome_id in enumerate(self.state.tome):
            if i > self.state.ingr.ingr[0]:
                continue # cannot learn, not enough tier-0 ingredients
            new_ingr = Ingr([actions[tome_id].tax_count-i,0,0,0]).apply(self.state.ingr)
            # todo ignoring my adding to tax_count now (I can increase it with my actions)
            # todo: the excess is discarded. manually update new_ingr to max 10

            copied_spells = copy.copy(self.state.spells)
            copied_spells.add(tome_id)
            copied_tome = copy.copy(self.state.tome)
            copied_tome.remove(tome_id)
            expanded.append(Node(State(new_ingr, copied_spells, copied_tome),
                                 self.f+1, copy.copy(self.history) + [tome_id]))

        # rest
        if len(self.state.spells) < len(spells):
            copied_spells = {s.id for s in spells}
            expanded.append(Node(State(self.state.ingr, copied_spells, self.state.tome),
                                 self.f+1, copy.copy(self.history) + [REST_ACTION.id]))
        # debug(f"Expanded {self} to {expanded}")
        return expanded

# seed=-4572190914680882200
class Search:
    def __init__(self, state, targets):
        self.state = state
        self.targets = targets

    def search(self):
        found = {}
        visited = set()
        curr_level = 1
        n_level_nodes = 0
        q = deque([Node(self.state, 1, [])])

        while len(q) > 0:
            node = q.popleft() ## take first element -> breadth-first
            if node.f > curr_level:
                # debug(f"{curr_level}: {n_level_nodes} processed")
                curr_level = node.f
                n_level_nodes = 0
                # so it ends sometime - just for profiling
                # if node.f > MAX_LEVEL:
                #     return found

            n_level_nodes+=1
            if node.state in visited:
                # debug(f"Already visited state {node.state}")
                continue

            curr_time=timeit.default_timer()
            if (curr_time-start_time) > TIME_THRES:
                debug(f"Time's up! Current level: {curr_level}")
                found[TIMEOUT_KEY] = TIMEOUT_KEY
                return found

            for target in self.targets:
                # todo consider just removing done goal from the targets, might be slightly quicker
                if node.satisfies(target) and target.id not in found.keys():
                    debug(f"Satisfied node: {node}")
                    found[target.id] = node
                    if len(found) == len(self.targets):
                        return found
            expanded = node.expand()
            q.extend(expanded) ## put at the end
            visited.add(node.state)
        debug("Cannot find a way to do some recipe :-(")
        return found
