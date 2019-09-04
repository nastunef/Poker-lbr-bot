from pypokerengine.api.game import setup_config, start_poker
import examples.players.fish_player as Fish
import lbr_player as Lbr
config = setup_config(max_round=10, initial_stack=1000, small_blind_amount=5)
config.register_player(name="p1", algorithm= Fish.FishPlayer())
config.register_player(name="p2", algorithm= Lbr.Lbr_player())
game_result = start_poker(config, verbose=1)