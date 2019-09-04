from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards
import lbr_utils
import math
import copy

NB_SIMULATION = 1

class Lbr_player(BasePokerPlayer):

    def __init__(self):
        self.probability_of_having_a_hand = []
        self.opponents_range = []
        self.probability_of_winning_hands = []

    def init_opponent_range(self, hole_card):
        self.opponents_range = []
        self.probability_of_having_a_hand = []
        unused = lbr_utils.unused_cards([], hole_card=hole_card)
        while unused != []:
            one_card = unused.pop(0)
            for two_card in unused:
                self.opponents_range.append([one_card, two_card])

        start_probablity = (1.0 / 50) * (1.0 / 49)
        for index_pair in range(len(self.opponents_range )):
            self.probability_of_having_a_hand.append(start_probablity)

    def init_probablitity_of_winning_hands(self):
        self.probability_of_winning_hands = [0 for i in range(len(self.opponents_range))]

    def update_opponent_range(self, community_card, coefficient_for_the_updates):

        if coefficient_for_the_updates:
            for hand_i in range(len(self.probability_of_having_a_hand)):
                self.probability_of_having_a_hand[hand_i] *= (1 - coefficient_for_the_updates[hand_i])
        else:
            num_unused_card = 50 - len(community_card)
            initial_probability = (1.0 / num_unused_card) * (1.0 / (num_unused_card - 1))
            for community_c in community_card:
                for pair in self.opponents_range:
                    if community_c in pair:
                        self.probability_of_having_a_hand.pop(self.opponents_range.index(pair))
                        self.opponents_range.remove(pair)
                    else:
                        self.probability_of_having_a_hand[self.opponents_range.index(pair)] = initial_probability

    def get_wp(self):
        result = 0
        for _ in range(len(self.probability_of_winning_hands)):
            result += self.probability_of_having_a_hand[_] * self.probability_of_winning_hands[_]
        return result


    def WpRollout(self, nb_simulation, hole_card, community_card):
        if not community_card:
            community_card = []
            self.init_opponent_range(hole_card)
            self.init_probablitity_of_winning_hands()
            for _ in range(nb_simulation):
                montecarlo_list = lbr_utils._montecarlo_simulation(hole_card, community_card, self.opponents_range)
                self.probability_of_winning_hands = lbr_utils.sum_list( self.probability_of_winning_hands , montecarlo_list)
            for _ in range(len(self.probability_of_having_a_hand)): self.probability_of_winning_hands[_] /= nb_simulation
            wp = self.get_wp()
        else:
            self.update_opponent_range(community_card=community_card, coefficient_for_the_updates=[])
            self.init_probablitity_of_winning_hands()
            num_community = len(community_card)
            need_card = 5 - num_community
            card_for_generate_combination_community = [0 for i in range(need_card)]
            unused_c = lbr_utils.unused_cards(community_card=community_card, hole_card=hole_card)
            num_iter = int(math.factorial(len(unused_c)) / (math.factorial(len(unused_c) - need_card) * math.factorial(need_card)))

            for _ in range(num_iter):
                if card_for_generate_combination_community:
                    new_community_card, unused = lbr_utils._get_community_combination(hole_card + community_card,
                                                                            card_for_generate_combination_community)
                    community_card += new_community_card
                montecarlo_list = lbr_utils._montecarlo_simulation(hole_card, community_card, self.opponents_range)
                self.probability_of_winning_hands = lbr_utils.sum_list(self.probability_of_winning_hands, montecarlo_list)
                if card_for_generate_combination_community:
                    for new_card in new_community_card: community_card.remove(new_card)
            for _ in range(len(self.probability_of_having_a_hand)): self.probability_of_winning_hands[_] /= num_iter
            wp = self.get_wp()
        return wp

    #  we define the logic to make an action through this method. (so this method would be the core of your ai)
    def declare_action(self, valid_actions, hole_card, round_state, opponents):

        pot = round_state['pot']['main']['amount']
        call_price = valid_actions[1]['amount']
        community_card = round_state['community_card']
        opponents = list(opponents.values())
        for opponent in opponents:
            if opponent != self:
                player = opponent

        wp = self.WpRollout( nb_simulation = NB_SIMULATION, hole_card = gen_cards(hole_card), community_card= gen_cards(community_card))
        asked = pot - call_price
        u_call =wp*pot - (1- wp)*asked
        h = [1.25, 1.5, 1.75, 2, 3]
        u_a = [u_call]
        a_value = [call_price]
        for step in h:
            a = step*call_price
            a_value.append(a)
            fp = 0
            pf = player.probability_of_fold(self.opponents_range)
            for hand_i in range(len(pf)):
                fp += self.probability_of_having_a_hand[hand_i]*pf[hand_i]

            copy_probability_of_having_a_hand = copy.deepcopy(self.probability_of_having_a_hand)
            self.update_opponent_range(community_card=None,coefficient_for_the_updates=pf)

            sum_probablity = sum(self.probability_of_having_a_hand)
            #нормируем
            for hand_prob in range(len(self.probability_of_having_a_hand)):
                self.probability_of_having_a_hand[hand_prob] =  self.probability_of_having_a_hand[hand_prob] / sum_probablity

            wp = self.get_wp()
            u_a.append(fp*pot + (1 - fp)*(wp*(pot + a) - (1 - wp)*(asked + a)))

            self.probability_of_having_a_hand = copy_probability_of_having_a_hand

        max_u = max(u_a)
        if max_u > 0:
            if a_value[u_a.index(max_u)] == call_price:
                action = {'action':'call', 'amount': call_price}
            else:
                action = {'action': 'raise', 'amount': a_value[u_a.index(max_u)] }
        else:
            action = valid_actions[0] # fetch fold action info

        return action['action'], action['amount']


    def receive_game_start_message(self, game_info):
        self.nb_player = game_info['player_num']

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


