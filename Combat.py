# Combat.py
from Attack import attack
import random

class Combat:
    def __init__(self, playerPokemon, opponentPokemon):
        self.player = playerPokemon
        self.opponent = opponentPokemon
    
    def player_attack(self, moveName):
        result = attack(moveName, self.player, self.opponent)
        return result
    
    def opponent_attack(self):
        moveName = random.choice(self.opponent.moveList)
        result = attack(moveName, self.opponent, self.player)
        return result
