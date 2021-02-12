import threading


class Character:
    lock = threading.Lock()

    def __init__(self, character_dict = None, table_object = None, monster = False):
        self.monster = monster
        if monster:
            self.join = True
            self.started = True
            self.ready = True
        else:
            self.started = False
            self.ready = False
        self.alive = True
        self.health = 100
        self.gold = 0
        self.room = 0
        if character_dict: self.add_from_dict(character_dict)
        elif table_object: self.add_from_table(table_object)
    
    def __setattr__(self, name, value):
        with self.lock:
            super().__setattr__(name, value)

    def add_from_dict(self, character_dict):
        self.name = character_dict['name']
        flags = character_dict['flags']
        flags = f'{flags:08b}'
        self.join = bool(int(flags[1]))
        self.attack = character_dict['attack']
        self.defense = character_dict['defense']
        self.regen = character_dict['regen']
        self.description = character_dict['text']

    def add_from_table(self, table_object):
        self.name = table_object.name
        self.attack = table_object.attack
        self.defense = table_object.defense
        self.regen = table_object.regen
        self.gold = table_object.gold
        self.description = table_object.description
        if self.monster:
            self.agro = 0 #table_object.agro

    def get_flags(self):
        flags = 128 if self.alive else 0
        flags += 64 if self.join else 0
        flags += 32 if self.monster else 0
        flags += 16 if self.started else 0
        flags += 8 if self.ready else 0
        return flags
    
    def set_flags(self, flags):
        flags = f'{flags:08b}'
        self.join = bool(int(flags[1]))
    
    def get_dict(self): # Returns a character dictionary ready to pass into LURKprot.encode()
        return {
            'name': self.name,
            'flags': self.get_flags(),
            'attack': self.attack,
            'defense': self.defense,
            'regen': self.regen,
            'health': self.health,
            'gold': self.gold,
            'room': self.room,
            'text': self.description
        }
    
    def get_fight_stats(self):
        if self.join:
            return {
                'name': self.name,
                'attack': self.attack,
                'defense': self.defense,
                'regen': self.regen,
                'health': self.health
            }
        else: return None


class Room:
    lock = threading.Lock()

    def __init__(self, number, name, description): # Init with number and name only, append to connections, characters, and lootables #
        self.number = number
        self.name = name
        self.description = description
        self.connections = [] # list of integer room numbers #
        self.players = [] # list of player names #
        self.monsters = {} # list of monster names
        self.lootables = [] # list of lootable names
    
    def __setattr__(self, name, value):
        with self.lock:
            # print(f'Character lock aquired in', threading.current_thread().name, 'for attribute', name, '=', value)
            super().__setattr__(name, value)

    def get_dict(self):
        dictionary = {
            'name': self.name,
            'room': self.number,
            'text': self.description
        }
        return dictionary


class Loot: # This will need to be some sort of protocal extension.

    def __init__(self, room, name, value, rewards, message):
        self.room = room
        self.name = name
        self.value = value # Gold
        self.rewards = rewards # Extra attack, defense, regen, or health
        self.message = message # A useful(or not so useful) clue


class Fight:

    def __init__(self):
        pass