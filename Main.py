import pygame
import sys
import os
import time

from Pokemon import Pokemon
from Pokedex import pokedex  # List of all Pokémon names (lowercase)
from Combat import Combat
from Attack import attack  # We'll directly call attack() for convenience

pygame.init()

# Screen setup
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pokémon Battle")

clock = pygame.time.Clock()
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (200, 200, 200)
GREEN = (0, 255, 0)
# Use a lighter green for Pokédex list buttons:
LIGHT_GREEN = (144, 238, 144)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)

# Game States
STATE_MENU    = "menu"
STATE_CHOOSE  = "choose"
STATE_BATTLE  = "battle"
STATE_POKEDEX = "pokedex"
STATE_RESULT  = "result"

state = STATE_MENU

# Team variables
TEAM_SIZE = 2
userTeam = []
cpuTeam  = []
picks = 0
userIndex = 0
cpuIndex  = 0

battle_log = []
winner = None

# Scroll offsets
choose_scroll_offset  = 0
pokedex_scroll_offset = 0

# Evolve/Devolve multipliers (default 1.0)
stats_multipliers = {}

# Selected Pokémon name for the Pokédex
selectedPokeName = None

# ------------------- LOAD BACKGROUNDS -------------------
menuBg = None
chooseBg = None
pokedexBg = None
battleBg = None

def load_image(path):
    if os.path.exists(path):
        img = pygame.image.load(path).convert()
        return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    return None

def load_backgrounds():
    global menuBg, chooseBg, pokedexBg, battleBg
    # Adjust these paths to match your folder structure:
    menuBg    = load_image(os.path.join("assets", "backgrounds", "backgroundmenu.png"))
    chooseBg  = load_image(os.path.join("assets", "backgrounds", "startbattlemenu.png"))
    pokedexBg = load_image(os.path.join("assets", "backgrounds", "pokedexmenu.jpg"))
    battleBg  = load_image(os.path.join("assets", "backgrounds", "battle.png"))

load_backgrounds()

# ------------------- MUSIC -------------------
music_menu    = os.path.join("assets", "music", "mainmenumusic.ogg")
music_battle  = os.path.join("assets", "music", "battlemusic.ogg")
music_pokedex = os.path.join("assets", "music", "pokedexmusic.mp3")

def play_music_for_state(st):
    pygame.mixer.music.stop()
    if st == STATE_MENU:
        if os.path.exists(music_menu):
            pygame.mixer.music.load(music_menu)
            pygame.mixer.music.play(-1)
    elif st in (STATE_CHOOSE, STATE_BATTLE):
        if os.path.exists(music_battle):
            pygame.mixer.music.load(music_battle)
            pygame.mixer.music.play(-1)
    elif st == STATE_POKEDEX:
        if os.path.exists(music_pokedex):
            pygame.mixer.music.load(music_pokedex)
            pygame.mixer.music.play(-1)

# ------------------- BUTTON UTILITY -------------------
class Button:
    def __init__(self, rect, text, callback, color=GREEN, text_color=BLACK, font_size=30):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.text_color = text_color
        self.font = pygame.font.SysFont(None, font_size)
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

def draw_text(surface, text, size, color, x, y, center=True):
    font = pygame.font.SysFont(None, size)
    txt_surf = font.render(text, True, color)
    if center:
        txt_rect = txt_surf.get_rect(center=(x, y))
    else:
        txt_rect = txt_surf.get_rect(topleft=(x, y))
    surface.blit(txt_surf, txt_rect)

# ------------------- EVOLUTION FUNCTIONS -------------------
def do_evolve(name):
    if name:
        evolve_pokemon(name)

def do_devolve(name):
    if name:
        devolve_pokemon(name)

# ------------------- ANIMATION HELPER -------------------
def animate_attack(pokemon, forward=True):
    if not hasattr(pokemon, "sprite_rect"):
        return
    direction = 1 if forward and (pokemon in userTeam) else -1 if forward else 0
    offset = 40 if forward else 0
    orig = pokemon.sprite_rect.x
    for _ in range(5):
        pokemon.sprite_rect.x += direction * (offset // 5)
        redraw_battle()
        pygame.time.delay(30)
    for _ in range(5):
        pokemon.sprite_rect.x -= direction * (offset // 5)
        redraw_battle()
        pygame.time.delay(30)
    pokemon.sprite_rect.x = orig

# ------------------- MENU -------------------
def start_battle():
    global state, picks, userTeam, cpuTeam, userIndex, cpuIndex
    userTeam.clear()
    cpuTeam.clear()
    picks = 0
    userIndex = 0
    cpuIndex = 0
    change_state(STATE_CHOOSE)

def view_pokedex():
    global selectedPokeName
    selectedPokeName = None
    change_state(STATE_POKEDEX)

def quit_game():
    pygame.quit()
    sys.exit()

menu_buttons = [
    Button((SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT*0.35, 200, 60), "Start Battle", start_battle, color=BLUE, text_color=WHITE, font_size=36),
    Button((SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT*0.45, 200, 60), "View Pokédex", view_pokedex, color=BLUE, text_color=WHITE, font_size=36),
    Button((SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT*0.55, 200, 60), "Quit", quit_game, color=RED, text_color=WHITE, font_size=36),
]

def redraw_menu():
    if menuBg:
        screen.blit(menuBg, (0, 0))
    else:
        screen.fill(WHITE)
    draw_text(screen, "Pokémon Battle", 72, BLACK, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.2)
    for btn in menu_buttons:
        btn.draw(screen)
    pygame.display.flip()

# ------------------- CHOOSE POKÉMON (TEAM PICK) -------------------
def get_available_pokemon():
    from Pokemon import Pokemon
    if not Pokemon.POKEMON_DICTIONARY:
        try:
            with open(os.path.join("Kanto Pokemon Spreadsheet.csv"), 'r') as fin:
                for line in fin:
                    line = line.strip()
                    if line:
                        pokeList = line.split(",")
                        Pokemon.POKEMON_DICTIONARY[pokeList[1]] = pokeList
        except Exception as e:
            print("Error loading CSV:", e)
    names = list(Pokemon.POKEMON_DICTIONARY.keys())
    names.sort()
    return names

choose_buttons = []

def update_choose_buttons():
    global choose_buttons, choose_scroll_offset
    choose_buttons = []
    names = get_available_pokemon()
    cols = 4
    x_gap = SCREEN_WIDTH * 0.18
    y_gap = SCREEN_HEIGHT * 0.1
    x_start = SCREEN_WIDTH * 0.1
    y_start = 200 + choose_scroll_offset  # Start lower to avoid overlap

    for i, name in enumerate(names):
        x = x_start + (i % cols) * x_gap
        y = y_start + (i // cols) * y_gap
        btn = Button((x, y, 140, 50), name, lambda n=name: choose_pokemon(n),
                     color=BLUE, text_color=WHITE, font_size=24)
        choose_buttons.append(btn)

def choose_pokemon(name):
    global picks, userTeam, cpuTeam
    p = Pokemon(name)
    factor = stats_multipliers.get(name, 1.0)
    p.battleHP    = int(p.battleHP    * factor)
    p.battleATK   = int(p.battleATK   * factor)
    p.battleDEF   = int(p.battleDEF   * factor)
    p.battleSpATK = int(p.battleSpATK * factor)
    p.battleSpDEF = int(p.battleSpDEF * factor)
    p.battleSpeed = int(p.battleSpeed * factor)
    if picks < TEAM_SIZE:
        userTeam.append(p)
    else:
        cpuTeam.append(p)
    picks += 1
    if picks >= TEAM_SIZE * 2:
        init_battle()
        change_state(STATE_BATTLE)

def init_battle():
    global battle_log, winner, userIndex, cpuIndex
    battle_log = []
    winner = None
    userIndex = 0
    cpuIndex = 0
    if userTeam and cpuTeam:
        battle_log.append(f"{userTeam[userIndex].name} vs {cpuTeam[cpuIndex].name}!")

def redraw_choose():
    if chooseBg:
        screen.blit(chooseBg, (0, 0))
    else:
        screen.fill(WHITE)
    draw_text(screen, "Pick Your Pokémon" if picks < TEAM_SIZE else "Pick CPU Pokémon",
              48, BLACK, SCREEN_WIDTH/2, 80)
    for btn in choose_buttons:
        btn.draw(screen)
    back_btn = Button((20, 20, 120, 40), "Back", lambda: change_state(STATE_MENU),
                      color=GRAY, text_color=BLACK, font_size=24)
    back_btn.draw(screen)
    pygame.display.flip()

# ------------------- BATTLE -------------------
move_buttons = []
defend_button = None
battle_back_btn = None

def current_user_pokemon():
    if userIndex < len(userTeam):
        return userTeam[userIndex]
    return None

def current_cpu_pokemon():
    if cpuIndex < len(cpuTeam):
        return cpuTeam[cpuIndex]
    return None

def update_move_buttons():
    global move_buttons, defend_button, battle_back_btn
    move_buttons = []
    poke = current_user_pokemon()
    if not poke:
        return
    moves = [poke.move1.name, poke.move2.name, poke.move3.name, poke.move4.name]
    x_start = SCREEN_WIDTH * 0.05
    y = SCREEN_HEIGHT - 100
    width = SCREEN_WIDTH * 0.15
    height = 40
    gap = SCREEN_WIDTH * 0.02
    for i, mv in enumerate(moves):
        x = x_start + i * (width + gap)
        btn = Button((x, y, width, height), mv, lambda m=mv: choose_move(m),
                     color=GREEN, text_color=BLACK, font_size=24)
        move_buttons.append(btn)
    defend_button = Button((SCREEN_WIDTH*0.75, y, width, height),
                           "Defend", choose_defend,
                           color=GRAY, text_color=BLACK, font_size=24)
    battle_back_btn = Button((20, 20, 100, 40), "Menu",
                             lambda: change_state(STATE_MENU),
                             color=GRAY, text_color=BLACK, font_size=24)

def choose_move(move_name):
    global battle_log, winner
    userPoke = current_user_pokemon()
    cpuPoke = current_cpu_pokemon()
    if not userPoke or not cpuPoke:
        return
    msg = attack(move_name, userPoke, cpuPoke)
    animate_attack(userPoke, forward=True)
    push_battle_log(msg)
    if not cpuPoke.isAlive():
        fainted_cpu()
        return
    msg2 = attack(cpuPoke.move1.name, cpuPoke, userPoke)
    animate_attack(cpuPoke, forward=True)
    push_battle_log(msg2)
    if not userPoke.isAlive():
        fainted_user()

def choose_defend():
    userPoke = current_user_pokemon()
    if not userPoke:
        return
    userPoke.defending = True
    push_battle_log(f"{userPoke.name} braces for impact!")
    cpuPoke = current_cpu_pokemon()
    if cpuPoke and cpuPoke.isAlive():
        msg = attack(cpuPoke.move1.name, cpuPoke, userPoke)
        animate_attack(cpuPoke, forward=True)
        push_battle_log(msg)
        if not userPoke.isAlive():
            fainted_user()

def fainted_cpu():
    global cpuIndex, winner, state
    poke = current_cpu_pokemon()
    push_battle_log(f"{poke.name} fainted!")
    cpuIndex += 1
    if cpuIndex >= TEAM_SIZE:
        winner = "User"
        change_state(STATE_RESULT)
    else:
        push_battle_log(f"{current_user_pokemon().name} vs {current_cpu_pokemon().name}!")

def fainted_user():
    global userIndex, winner, state
    poke = current_user_pokemon()
    push_battle_log(f"{poke.name} fainted!")
    userIndex += 1
    if userIndex >= TEAM_SIZE:
        winner = "CPU"
        change_state(STATE_RESULT)
    else:
        push_battle_log(f"{current_user_pokemon().name} vs {current_cpu_pokemon().name}!")

def push_battle_log(msg):
    global battle_log
    lines = msg.split("\n")
    for ln in lines:
        battle_log.append(ln)
    while len(battle_log) > 4:
        battle_log.pop(0)

def redraw_battle():
    if battleBg:
        screen.blit(battleBg, (0, 0))
    else:
        screen.fill(WHITE)
    userPoke = current_user_pokemon()
    cpuPoke = current_cpu_pokemon()
    if userPoke and not hasattr(userPoke, "sprite_rect"):
        userPoke.sprite = userPoke.load_sprite()
        if userPoke.sprite:
            userPoke.sprite = pygame.transform.scale(userPoke.sprite, (300, 300))
        userPoke.sprite_rect = pygame.Rect(80, 250, 300, 300)
    if cpuPoke and not hasattr(cpuPoke, "sprite_rect"):
        cpuPoke.sprite = cpuPoke.load_sprite()
        if cpuPoke.sprite:
            cpuPoke.sprite = pygame.transform.scale(cpuPoke.sprite, (300, 300))
        cpuPoke.sprite_rect = pygame.Rect(SCREEN_WIDTH-380, 250, 300, 300)
    if userPoke and userPoke.sprite:
        screen.blit(userPoke.sprite, userPoke.sprite_rect)
        draw_text(screen, f"HP: {userPoke.battleHP}", 24, BLACK,
                  userPoke.sprite_rect.x, userPoke.sprite_rect.y - 30, center=False)
    if cpuPoke and cpuPoke.sprite:
        screen.blit(cpuPoke.sprite, cpuPoke.sprite_rect)
        draw_text(screen, f"HP: {cpuPoke.battleHP}", 24, BLACK,
                  cpuPoke.sprite_rect.x, cpuPoke.sprite_rect.y - 30, center=False)
    log_rect = pygame.Rect(50, 120, SCREEN_WIDTH - 100, 120)
    s = pygame.Surface((log_rect.width, log_rect.height))
    s.set_alpha(180)
    s.fill(GRAY)
    screen.blit(s, (log_rect.x, log_rect.y))
    log_y = log_rect.y + 10
    for msg in battle_log:
        draw_text(screen, msg, 24, BLACK, SCREEN_WIDTH/2, log_y)
        log_y += 28
    for btn in move_buttons:
        btn.draw(screen)
    if defend_button:
        defend_button.draw(screen)
    if battle_back_btn:
        battle_back_btn.draw(screen)
    pygame.display.flip()

# ------------------- POKEDEX -------------------
def calc_effective_stats(name):
    from Pokemon import Pokemon
    if name not in Pokemon.POKEMON_DICTIONARY:
        return {}
    pokeList = Pokemon.POKEMON_DICTIONARY[name]
    baseHP = int(pokeList[4])
    baseATK = int(pokeList[5])
    baseDEF = int(pokeList[6])
    baseSpA = int(pokeList[7])
    baseSpD = int(pokeList[8])
    baseSpe = int(pokeList[9])
    IV = 30
    EV = 85
    factor = stats_multipliers.get(name, 1.0)
    hp  = int(baseHP + (0.5*IV) + (0.125*EV) + 60)
    atk = baseATK + (0.5*IV) + (0.125*EV) + 5
    dfn = baseDEF + (0.5*IV) + (0.125*EV) + 5
    spa = baseSpA + (0.5*IV) + (0.125*EV) + 5
    spd = baseSpD + (0.5*IV) + (0.125*EV) + 5
    spe = baseSpe + (0.5*IV) + (0.125*EV) + 5
    hp  = int(hp * factor)
    atk = int(atk * factor)
    dfn = int(dfn * factor)
    spa = int(spa * factor)
    spd = int(spd * factor)
    spe = int(spe * factor)
    return {'HP': hp, 'ATK': atk, 'DEF': dfn, 'SPATK': spa, 'SPDEF': spd, 'SPEED': spe}

def evolve_pokemon(name):
    current = stats_multipliers.get(name, 1.0)
    stats_multipliers[name] = current * 2.0
    print(f"{name} evolved -> multiplier = {stats_multipliers[name]}")

def devolve_pokemon(name):
    current = stats_multipliers.get(name, 1.0)
    stats_multipliers[name] = current * 0.5
    print(f"{name} devolved -> multiplier = {stats_multipliers[name]}")

def redraw_pokedex():
    if pokedexBg:
        screen.blit(pokedexBg, (0, 0))
    else:
        screen.fill(WHITE)
    draw_text(screen, "Pokédex", 60, BLACK, SCREEN_WIDTH/2, 80)
    back_btn = Button((20, 20, 120, 40), "Back", lambda: change_state(STATE_MENU),
                      color=GRAY, text_color=BLACK, font_size=24)
    back_btn.draw(screen)
    y = 200 + pokedex_scroll_offset
    names = get_available_pokemon()
    pokemon_buttons = []
    for name in names:
        if y + 40 > 0 and y < SCREEN_HEIGHT:
            name_btn = Button((80, y, 140, 40), name,
                              lambda n=name: select_pokedex_pokemon(n),
                              color=LIGHT_GREEN, text_color=BLACK, font_size=24)
            name_btn.draw(screen)
            pokemon_buttons.append((name_btn, name))
        y += 50
    if selectedPokeName:
        stats = calc_effective_stats(selectedPokeName)
        panel_rect = pygame.Rect(SCREEN_WIDTH - 420, 200, 400, 300)
        s = pygame.Surface((panel_rect.width, panel_rect.height))
        s.set_alpha(200)
        s.fill(WHITE)
        screen.blit(s, panel_rect)
        draw_text(screen, f"{selectedPokeName} Stats:", 30, BLACK,
                  panel_rect.x + 20, panel_rect.y + 20, center=False)
        if stats:
            lines = [
                f"HP: {stats['HP']}",
                f"ATK: {stats['ATK']}",
                f"DEF: {stats['DEF']}",
                f"SP.ATK: {stats['SPATK']}",
                f"SP.DEF: {stats['SPDEF']}",
                f"SPEED: {stats['SPEED']}"
            ]
            line_y = panel_rect.y + 60
            for ln in lines:
                draw_text(screen, ln, 24, BLACK, panel_rect.x + 20, line_y, center=False)
                line_y += 30
            evolve_btn = Button((panel_rect.x + 20, panel_rect.y + 240, 100, 40),
                                "Evolve",
                                lambda: do_evolve(selectedPokeName),
                                color=BLUE, text_color=WHITE, font_size=20)
            devolve_btn = Button((panel_rect.x + 140, panel_rect.y + 240, 100, 40),
                                 "Devolve",
                                 lambda: do_devolve(selectedPokeName),
                                 color=RED, text_color=WHITE, font_size=20)
            evolve_btn.draw(screen)
            devolve_btn.draw(screen)
            multiplier = stats_multipliers.get(selectedPokeName, 1.0)
            if multiplier != 1.0:
                mult_text = f"Power Level: {multiplier:.1f}x"
                draw_text(screen, mult_text, 20, BLACK, panel_rect.x + 20, panel_rect.y + 200, center=False)
    pygame.display.flip()

def select_pokedex_pokemon(name):
    global selectedPokeName
    selectedPokeName = name
    print(f"Clicked on {name} in the Pokédex.")

# ------------------- RESULT -------------------
result_back_btn = None

def redraw_result():
    global result_back_btn
    screen.fill(WHITE)
    if winner == "User":
        result_text = "You Win!"
    elif winner == "CPU":
        result_text = "CPU Wins!"
    else:
        result_text = "Battle Over"
    draw_text(screen, result_text, 64, BLACK, SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
    result_back_btn = Button((SCREEN_WIDTH/2 - 75, SCREEN_HEIGHT - 100, 150, 60),
                             "Main Menu", lambda: change_state(STATE_MENU),
                             color=GRAY, text_color=BLACK, font_size=32)
    result_back_btn.draw(screen)
    pygame.display.flip()

# ------------------- CHANGE STATE -------------------
def change_state(new_state):
    global state, battle_log, winner, userTeam, cpuTeam, userIndex, cpuIndex, selectedPokeName
    state = new_state
    play_music_for_state(state)
    if state == STATE_MENU:
        battle_log = []
        winner = None
        userTeam.clear()
        cpuTeam.clear()
        userIndex = 0
        cpuIndex = 0
        selectedPokeName = None

# ------------------- MAIN LOOP -------------------
running = True
play_music_for_state(state)

while running:
    clock.tick(FPS)
    if state == STATE_MENU:
        redraw_menu()
    elif state == STATE_CHOOSE:
        update_choose_buttons()
        redraw_choose()
    elif state == STATE_BATTLE:
        update_move_buttons()
        redraw_battle()
    elif state == STATE_POKEDEX:
        redraw_pokedex()
    elif state == STATE_RESULT:
        redraw_result()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            quit_game()
        # Only respond to left mouse button clicks:
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if state == STATE_MENU:
                for btn in menu_buttons:
                    if btn.is_clicked(pos):
                        btn.callback()
            elif state == STATE_CHOOSE:
                for btn in choose_buttons:
                    if btn.is_clicked(pos):
                        btn.callback()
                if pygame.Rect(20, 20, 120, 40).collidepoint(pos):
                    change_state(STATE_MENU)
            elif state == STATE_BATTLE:
                if defend_button and defend_button.is_clicked(pos):
                    defend_button.callback()
                for btn in move_buttons:
                    if btn.is_clicked(pos):
                        btn.callback()
                if battle_back_btn and battle_back_btn.is_clicked(pos):
                    battle_back_btn.callback()
            elif state == STATE_POKEDEX:
                if pygame.Rect(20, 20, 120, 40).collidepoint(pos):
                    change_state(STATE_MENU)
                # Check for Pokémon selection:
                y = 200 + pokedex_scroll_offset
                for name in get_available_pokemon():
                    button_rect = pygame.Rect(80, y, 140, 40)
                    if button_rect.collidepoint(pos):
                        select_pokedex_pokemon(name)
                        break
                    y += 50
                # Check evolve/devolve buttons
                if selectedPokeName:
                    panel_rect = pygame.Rect(SCREEN_WIDTH - 420, 200, 400, 300)
                    evolve_btn = pygame.Rect(panel_rect.x + 20, panel_rect.y + 240, 100, 40)
                    devolve_btn = pygame.Rect(panel_rect.x + 140, panel_rect.y + 240, 100, 40)
                    if evolve_btn.collidepoint(pos):
                        do_evolve(selectedPokeName)
                    elif devolve_btn.collidepoint(pos):
                        do_devolve(selectedPokeName)
            elif state == STATE_RESULT:
                if result_back_btn and result_back_btn.is_clicked(pos):
                    result_back_btn.callback()
        elif event.type == pygame.MOUSEWHEEL:
            if state == STATE_CHOOSE:
                choose_scroll_offset += event.y * 20
            elif state == STATE_POKEDEX:
                pokedex_scroll_offset += event.y * 20
                max_scroll = -max(0, len(get_available_pokemon()) * 50 - (SCREEN_HEIGHT - 200))
                pokedex_scroll_offset = min(0, max(max_scroll, pokedex_scroll_offset))
    pygame.display.update()
pygame.quit()
sys.exit()
