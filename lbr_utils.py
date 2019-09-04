from pypokerengine.engine.hand_evaluator import HandEvaluator
import random
from pypokerengine.engine.card import Card
def _montecarlo_simulation(hole_card, community_card, range_opponent):

    community_card = _fill_community_card(community_card, used_card = hole_card + community_card)
    opponents_score = [HandEvaluator.eval_hand(hole, community_card) for hole in range_opponent]
    my_score = HandEvaluator.eval_hand(hole_card, community_card)
    score = []
    for opp_score in opponents_score:
        if my_score > opp_score:
            score.append(1)
        else:
            score.append(0)
    return score

def _fill_community_card(base_cards, used_card):
    need_num = 5 - len(base_cards)
    if need_num == 0: return base_cards
    return base_cards + _pick_unused_card(need_num, used_card)

#неиспользуемые карты
def unused_cards(community_card, hole_card):
    used_cards = community_card + hole_card
    used = [card.to_id() for card in used_cards]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]
    return [Card.from_id(card_id) for card_id in unused]

def _pick_unused_card(card_num, used_card):
    used = [card.to_id() for card in used_card]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]
    choiced = random.sample(unused, card_num)
    return [Card.from_id(card_id) for card_id in choiced]

def _get_community_combination(used_card, card_for_generate_combination):
    used = [card.to_id() for card in used_card]
    unused = [card_id for card_id in range(1, 53) if card_id not in used]

    if card_for_generate_combination[0] == 0:
        for num in range(len(card_for_generate_combination)):
            card_for_generate_combination[num] = unused.pop(0)

    unused, choiced_to_id = return_num(len(card_for_generate_combination)-1, unused, card_for_generate_combination)

    return [Card.from_id(card_id) for card_id in choiced_to_id], unused

def return_num(index, unused_card, all_num):
    unused_card = append_and_sort(unused_card, all_num[index])
    if all_num[index] >= max(unused_card):
        unused_card,all_num = return_num(index-1, unused_card, all_num)
        all_num[index],unused_card = set_next_num(unused_card,all_num[index-1])
    else:
        all_num[index], unused_card = set_next_num_in_unused(unused_card,all_num[index])
    return unused_card, all_num

def set_next_num(unused, num):
    for i in range(len(unused)):
        if unused[i] > num:
            num_next = unused[i]
            unused.pop(i)
            break
    return num_next, unused

def set_next_num_in_unused(unused, num):
    index = unused.index(num)
    num_next = unused[index + 1]
    unused.pop(index + 1)
    return num_next, unused

def append_and_sort(list_for_sort, num):
    list_for_sort.append(num)
    list_for_sort.sort()
    return list_for_sort

def sum_list(l1, l2):
    for i in range(len(l1)): l1[i] += l2[i]
    return l1