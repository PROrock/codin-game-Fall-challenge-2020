import sys
import math
from operator import add


class Action:
    def __init__(self, id, kind, ingr, price):
        self.id = id
        self.kind = kind
        self.ingr = ingr
        self.price = price 

    def apply(self, score):
        inventory = list(map(add, score.ingr, self.ingr) )
        return Action(-1, None, inventory, score.price + self.price)

    def is_valid(self):
        return all((i>=0 for i in self.ingr))

    def __repr__(self):
       return (f'{self.__class__.__name__}('
               f'{self.id!r}, {self.kind!r}, {self.ingr!r}, {self.price!r})')


class Recipe(Action):
    def __init__(self, id, ingr, price):
        super().__init__(id, "BREW", ingr, price)

class Spell(Action):
    def __init__(self, id, kind, ingr, price, castable):
        super().__init__(id, kind, ingr, price)
        self.castable = castable 


def best_recipe():
    for recipe in recipes:
        new_score = recipe.apply(my_score)
        # print(f"New score {new_score}", file=sys.stderr, flush=True)
        if new_score.is_valid():
            return f"BREW {recipe.id}"
    return None

def best_spell():
    for spell in spells:
        if not spell.castable:
            continue
        new_score = spell.apply(my_score)
        # print(f"New score {new_score}", file=sys.stderr, flush=True)
        if new_score.is_valid():
            return f"CAST {spell.id}"
    return None


# game loop
while True:
    recipes = []
    spells = []

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
        price = int(price)
        tome_index = int(tome_index)
        tax_count = int(tax_count)
        castable = castable != "0"
        repeatable = repeatable != "0"

        if action_type == 'BREW':
            recipes.append(Recipe(action_id, [delta_0,delta_1,delta_2,delta_3], price))
        elif action_type == 'CAST':
            spells.append(Spell(action_id, action_type, [delta_0,delta_1,delta_2,delta_3], price, castable))


    score_line = [int(j) for j in input().split()]
    my_score = Recipe(-1, score_line[:4], score_line[4])
    score_line = [int(j) for j in input().split()]
    opp_score = Recipe(-1, score_line[:4], score_line[4])
    # for i in range(2):
    #     # inv_0: tier-0 ingredients in inventory
    #     # score: amount of rupees
    #     inv_0, inv_1, inv_2, inv_3, score = [int(j) for j in input().split()]


    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)

    # first try to brew if we can
    action = best_recipe()

    if not action:
        action = best_spell()
    if not action:
        action = "REST zzZZ"

    # in the first league: BREW <id> | WAIT; later: BREW <id> | CAST <id> [<times>] | LEARN <id> | REST | WAIT
    print(action)
