from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Boolean, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine('sqlite:///game.db')

Base = declarative_base()
Session = sessionmaker(bind = engine)


# class Player(Base):
#     __tablename__ = 'player'
#     id = Column(Integer, primary_key = True)


class Monster(Base):
    __tablename__ = 'monster'
    id = Column(Integer, primary_key = True)
    name = Column(String(32), nullable = False, unique = True)
    attack = Column(Integer, nullable = False)
    defense = Column(Integer, nullable = False)
    regen = Column(Integer, nullable = False)
    health = Column(Integer, nullable = False)
    gold = Column(Integer, nullable = False)
    room = Column(Integer, nullable = False)
    description = Column(String(256), nullable = False)

    def __init__(self, name, attack, defense, regen, health, gold, room, description):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.regen = regen
        self.health = health
        # self.agro = agro
        self.gold = gold
        self.room = room
        self.description = description


class Character:
    __tablename__ = 'character'
    id = Column(Integer, primary_key = True)
    alive = Column(Boolean, nullable = False)
    join = Column(Boolean, nullable = False)
    monster = Column(Boolean, nullable = False)
    started = Column(Boolean, nullable = False)
    ready = Column(Boolean, nullable = False)
    name = Column(String(32), nullable = False, unique = True)
    attack = Column(Integer, nullable = False)
    defense = Column(Integer, nullable = False)
    regen = Column(Integer, nullable = False)
    health = Column(Integer, nullable = False)
    gold = Column(Integer, nullable = False)
    room = Column(Integer, nullable = False)
    description = Column(String(256), nullable = False)

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


class Room(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key = True)
    name = Column(String(32), nullable = False)
    description = Column(String(256), nullable = False)

    def __init__(self, name, description):
        self.name = name
        self.description = description


class Connection(Base):
    __tablename__ = 'connection'
    id = Column(Integer, primary_key = True)
    room1 = Column(Integer, nullable = False)
    room2 = Column(Integer, nullable = False)
    condition = Column(String(256)) # monster_name: dead, capacity: > 10, capacity == 1 

    def __init__(self, room1, room2):
        self.room1 = room1
        self.room2 = room2
        self.condition = ''
    
    def __repr__(self):
        return f'{self.room1} -> {self.room2}'


class Loot(Base):
    __tablename__ = 'loot'
    id = Column(Integer, primary_key = True)
    room = Column(Integer, nullable = False)
    name = Column(String(32), nullable = False)
    value = Column(Integer, nullable = False)
    rewards = Column(String(256))
    message = Column(String(256))
    condition = Column(String(256)) # monster_name: dead, capacity: > 10, capacity == 1 

    def __init__(self, name, value, rewards, message, condition):
        self.name = name
        self.value = value
        self.rewards = rewards
        self.message = message
        self.condition = condition


Base.metadata.create_all(bind = engine)