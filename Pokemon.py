import os
import pygame
from Move import Move

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CSV file is in the same folder as this file.
CSV_FILE = os.path.join(BASE_DIR, "Kanto Pokemon Spreadsheet.csv")

class Pokemon(object):
    POKEMON_DICTIONARY = {}
    IV = 30
    EV = 85
    STAB = 1.5
    LEVEL = 50

    def __init__(self, pokemon):
        pokemonInfo = []
        if len(Pokemon.POKEMON_DICTIONARY) == 0:
            try:
                with open(CSV_FILE, 'r') as fin:
                    for line in fin:
                        line = line.strip()
                        if line:
                            pokeList = line.split(",")
                            Pokemon.POKEMON_DICTIONARY[pokeList[1]] = pokeList
            except Exception as e:
                print("Error reading CSV:", e)
        for key in Pokemon.POKEMON_DICTIONARY:
            if key.lower() == pokemon.lower():
                pokemonInfo = Pokemon.POKEMON_DICTIONARY[key]
        self.__id = pokemonInfo[0] if len(pokemonInfo) > 0 else ""
        self.name = pokemonInfo[1] if len(pokemonInfo) > 1 else ""
        self.level = Pokemon.LEVEL
        self.type1 = pokemonInfo[2] if len(pokemonInfo) > 2 else ""
        self.type2 = pokemonInfo[3] if len(pokemonInfo) > 3 else ""
        self.__hp = int(pokemonInfo[4]) if len(pokemonInfo) > 4 else 0
        self.__atk = int(pokemonInfo[5]) if len(pokemonInfo) > 5 else 0
        self.__defense = int(pokemonInfo[6]) if len(pokemonInfo) > 6 else 0
        self.__spAtk = int(pokemonInfo[7]) if len(pokemonInfo) > 7 else 0
        self.__spDef = int(pokemonInfo[8]) if len(pokemonInfo) > 8 else 0
        self.__speed = int(pokemonInfo[9]) if len(pokemonInfo) > 9 else 0

        self.battleHP = int(self.__hp + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 60)
        self.battleATK = self.__atk + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.battleDEF = self.__defense + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.battleSpATK = self.__spAtk + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.battleSpDEF = self.__spDef + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.battleSpeed = self.__speed + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5

        self.originalATK = self.__atk + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.originalDEF = self.__defense + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.originalSpATK = self.__spAtk + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.originalSpDEF = self.__spDef + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5
        self.originalSpeed = self.__speed + (0.5 * Pokemon.IV) + (0.125 * Pokemon.EV) + 5

        self.move1 = Move(pokemonInfo[10]) if len(pokemonInfo) > 10 else Move("")
        self.move2 = Move(pokemonInfo[11]) if len(pokemonInfo) > 11 else Move("")
        self.move3 = Move(pokemonInfo[12]) if len(pokemonInfo) > 12 else Move("")
        self.move4 = Move(pokemonInfo[13]) if len(pokemonInfo) > 13 else Move("")
        self.moveList = [self.move1.name.lower(), self.move2.name.lower(),
                         self.move3.name.lower(), self.move4.name.lower()]

        self.atkStage = 0
        self.defStage = 0
        self.spAtkStage = 0
        self.spDefStage = 0
        self.speedStage = 0

        self.defending = False

        self.sprite = None

    def load_sprite(self):
        sprite_path_png = os.path.join("Sprites", self.name.lower() + ".png")
        sprite_path_gif = os.path.join("Sprites", self.name.lower() + ".gif")
        placeholder = os.path.join("Sprites", "placeholder.png")
        try:
            if os.path.exists(sprite_path_png):
                sprite = pygame.image.load(sprite_path_png).convert_alpha()
            elif os.path.exists(sprite_path_gif):
                sprite = pygame.image.load(sprite_path_gif).convert_alpha()
            else:
                sprite = pygame.image.load(placeholder).convert_alpha()
        except Exception as e:
            print("Error loading sprite for", self.name, ":", e)
            sprite = None
        return sprite

    def __str__(self):
        msg = (f"Name: {self.name}\nID: {self.__id}\nType1: {self.type1}\nType2: {self.type2}\n"
               f"Base HP: {self.__hp}\nBase ATK: {self.__atk}\nBase DEF: {self.__defense}\n"
               f"Base Sp. ATK: {self.__spAtk}\nBase Sp. DEF: {self.__spDef}\nBase Speed: {self.__speed}")
        return msg

    def getName(self):
        return self.name

    def getLevel(self):
        return self.level

    def getHP(self):
        return self.__hp

    def getATK(self):
        return self.__atk

    def getDEF(self):
        return self.__defense

    def getSpATK(self):
        return self.__spAtk

    def getSpDEF(self):
        return self.__spDef

    def getSpeed(self):
        return self.__speed

    def printHP(self):
        return f"{self.name}: HP {self.battleHP}"

    def printMoves(self):
        return (f"Move 1: {self.move1.moveInfo[1]}\nMove 2: {self.move2.moveInfo[1]}\n"
                f"Move 3: {self.move3.moveInfo[1]}\nMove 4: {self.move4.moveInfo[1]}")

    def useMove(self, move):
        return f"{self.name} used {move.name}!"

    def loseHP(self, lostHP):
        self.battleHP -= lostHP
        if self.battleHP < 0:
            self.battleHP = 0
        return f"{self.name} lost {lostHP} HP!"

    def gainHP(self, gainedHP):
        self.__hp += gainedHP

    def isAlive(self):
        return self.battleHP > 0

    def faint(self):
        if self.battleHP <= 0:
            return f"{self.name} fainted!"
        return ""
