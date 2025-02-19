# Pokedex.py
# This file reads through the Kanto Pokémon Spreadsheet and creates a list of all Pokémon names called "pokedex"
pokedex = []
pokemonDictionary = {}
try:
    fin = open("Kanto Pokemon Spreadsheet.csv", 'r')
    for line in fin:
        line = line.strip()
        if line:
            pokeList = line.split(",")
            pokemonDictionary[pokeList[1]] = pokeList
    fin.close()
except Exception as e:
    print("Error reading Kanto Pokemon Spreadsheet.csv:", e)

for key in pokemonDictionary:
    pokedex.append(key.lower())
pokedex.sort()
