
from tkinter import Tk, Frame, Listbox, Label, Text, StringVar, BooleanVar, Entry, EXTENDED, MULTIPLE, SINGLE, INSERT, END, ACTIVE, N, S, E, W
from tkinter import ttk
from tkinter.scrolledtext import *
from LURKp import LURKp
import time, threading

### Character Stats ###
character_dict = {
    'name': '', # 31 bytes
    'flags': 0b01000000, # 1 byte
    'attack': 34, # 2 bytes
    'defense': 33,  # 2 bytes
    'regen': 33, # 2 bytes
    'health': 0, # 2 bytes
    'gold': 0, # 2 bytes
    'room': 0, # 2 bytes
    'text': 'BA SpeLURKer' # desc-len bytes
}

current_room = {
    'name': None,
    'number': None,
    'desc': None
}

### Connection Settings ###
host = 'isoptera.lcsc.edu'
port = 5051

### Global Objects and Variables ###
window = Tk()
window.title('LURKle')

ptc = LURKp(host, port) # LURK protocol class

players_dict = {}
monsters_dict = {}
connections_list = []

input_user = StringVar()
input_type = 0

def join_recv(*args):
    print(exit_flag.get(), recv_thread.is_alive())
    if exit_flag.get() and recv_thread.is_alive():
        print('Attempting to Join recv_thread')
        recv_thread.join()
        print('Thread joined succesfully!')

exit_flag = BooleanVar()
exit_flag.set(False)
exit_flag.trace('w', join_recv)


### Function Definitions ###

def console(message, sender = None, recipient = None, end = '\n', level = 0):
    global text
    if level: # TODO: Set color formatting on [sender]
        if level == 1: color = 'Green' # Successful Action
        elif level == 2: color = 'Yellow' # Unsuccessful action
        elif level == 3: color = 'Red' # Server Critical Issue
        elif level == 4: color = 'blue' # Private Message
    # TODO: set bold formatting on [sender]
    if not sender:
        sender = 'LURKle'
    if not recipient:
        text.insert('0.0', f'[{sender}]: {message}{end}')
    else:
        text.insert('0.0', f'[{sender}]->{recipient}: {message}{end}')

def get_input():
    input_get = input_field.get()
    input_user.set('')
    return input_get

def enter_pressed(event):
    input_get = get_input()
    if input_get:
        if not input_type:
            selections = players.curselection()
            if selections:
                recipients = [players.get(i).split()[0] for i in selections]
                console(input_get, sender = character_dict['name'], recipient = recipients)
                for player in recipients:
                    ptc.send_chat(input_get, target = player)

### Protocol Functions ###

def join_server(): ### Connects to server, receives version and extension info ###
    global character_dict
    join_name = get_input()
    if join_name:
        character_dict['name'] = join_name
        console(f'Joining server as {join_name}')
        ptc.join_server(join_name)
    else:
        console('Enter a name and click JOIN')

def start(): ### Starts a game with server ###
    global character_dict, recv_thread, exit_flag
    exit_flag.set(False)
    if ptc.conn.connect and not recv_thread.is_alive():
        recv_thread.start()
    ptc.send_character(character_dict)
    ptc.start()

def change_room():
    global connections, connections_list, players_dict, monsters_dict
    selection = connections.curselection()
    if selection:
        room = connections_list[selection[0]]
        print(room)
        room = int(room[1])
        ptc.change_room(room)
        players_dict.clear()
        monsters_dict.clear()
        connections_list.clear()
    else:
        console('Select a connecting room and click ROOM')

def fight():
    ptc.fight()

def pvp_fight():
    global players
    target = players.curselection()
    if target:
        target = players.get(target[0]).split()[0]
        ptc.fight(target)
    else:
        console('Select a target and click PVPFight')

def loot():
    global monsters, players
    target = monsters.curselection()
    if target:
        target = monsters.get(target).split()[0]
        ptc.loot(target)
    else:
        targets = players.curselection()
        if targets:
            targets = [players.get(i).split()[0] for i in targets]
            for target in targets:
                ptc.loot(target)
        else:
            console('Select a target and click LOOT')

def leave():
    global recv_thread
    if ptc.conn.connected:
        ptc.leave_server()
    


### Current Room Frame ###
room_frame = Frame(window, width = 100)
room_label = Label(room_frame, text = 'Current Room:')
room_value = Label(room_frame, text = '')
room_desc_label = Label(room_frame, text = 'Description:')
room_desc_text = Text(room_frame, height = 3)

def update_room():
    global current_room, room_value, room_desc_text
    room_value['text'] = f"{current_room['name']}\t{current_room['number']}"
    room_desc_text.delete('0.0', END)
    room_desc_text.insert('0.0', current_room['desc'])


### Select Frame ###
select_frame = Frame(window)
players_label = Label(select_frame, text = 'Players in Room')
players = Listbox(select_frame, selectmode = MULTIPLE, width=28, height=10, relief = 'sunken')
monsters_label = Label(select_frame, text = 'Monsters in Room')
monsters = Listbox(select_frame, selectmode = SINGLE, width=28, height=5, relief = 'sunken')
connections_label = Label(select_frame, text = 'Connecting Rooms')
connections = Listbox(select_frame, selectmode = SINGLE, width=28, height=6, relief = 'sunken')

def update_players():
    global players, players_dict
    players.delete(0, END)
    players_list = sorted(players_dict.keys())
    for player in players_list:
        text = f"{player[:10]:15}\t{players_dict[player]['flags']};{players_dict[player]['health']};{players_dict[player]['gold']}"
        players.insert(END, text)

def update_monsters():
    global monsters, monsters_list
    monsters.delete(0, END)
    monsters_list = sorted(monsters_dict.keys())
    for monster in monsters_list:
        text = f"{monster[:10]:15}\t{monsters_dict[monster]['flags']};{monsters_dict[monster]['health']};{monsters_dict[monster]['gold']}"
        monsters.insert(END, text)

def update_connections():
    global connections, connections_list
    connections.delete(0, END)
    connections_list = sorted(connections_list)
    for name, number in connections_list:
        connections.insert(END, f'{number}\t{name}')

### Message Frame ###
chat_frame = Frame(window)
text = ScrolledText(chat_frame, width=80, height=30, borderwidth = 1, relief = 'sunken')
input_field = Entry(chat_frame, text = input_user, width = 69, relief = 'sunken')

### Right-Hand Frame ###
right_frame = Frame(window)

### Stats Frame ###
stats_frame = Frame(right_frame) # width = 100, height = 300
name_label = Label(stats_frame, text = 'Name:')
attack_label = Label(stats_frame, text = 'Attack:')
defense_label = Label(stats_frame, text = 'Defense:')
regen_label = Label(stats_frame, text = 'Regen:')
health_label = Label(stats_frame, text = 'Health:')
gold_label = Label(stats_frame, text = 'Gold:')
alive_label = Label(stats_frame, text = 'Alive:')
fight_label = Label(stats_frame, text = 'Fight:')
name_value = Label(stats_frame, text = character_dict['name'])
attack_value = Label(stats_frame, text = character_dict['attack'])
defense_value = Label(stats_frame, text = character_dict['defense'])
regen_value = Label(stats_frame, text = character_dict['regen'])
health_value = Label(stats_frame, text = character_dict['health'])
gold_value = Label(stats_frame, text = character_dict['gold'])
alive_value = Label(stats_frame, text = 'Alive:')
fight_value = Label(stats_frame, text = 'Fight:')

def update_stats(dict):
    global character_dict, name_value, attack_value, defense_value, regen_value, health_value, gold_value
    if not dict:
        dict = character_dict
    name_value['text'] = dict['name']
    attack_value['text'] = dict['attack']
    defense_value['text'] = dict['defense']
    regen_value['text'] = dict['regen']
    health_value['text'] = dict['health']
    gold_value['text'] = dict['gold']
    alive_value['text'] = dict['alive']
    fight_value['text'] = dict['join']

### Button Frame ###
button_width = 7
button_frame = Frame(right_frame) # , width = 100, height = 300
join_button = ttk.Button(button_frame, text = 'JOIN', command = join_server, width = button_width)
start_button = ttk.Button(button_frame, text = 'START', command = start, width = button_width)
room_button = ttk.Button(button_frame, text = 'ROOM', command = change_room, width = button_width)
fight_button = ttk.Button(button_frame, text = 'Fight', command = fight, width = button_width)
pvp_fight_button = ttk.Button(button_frame, text = 'PVPFight', command = pvp_fight, width = button_width)
loot_button = ttk.Button(button_frame, text = 'LOOT', command = loot, width = button_width)
leave_button = ttk.Button(button_frame, text = 'LEAVE', command = leave, width = button_width)


### Grid Alignment ###
room_frame.grid(row = 1, columnspan = 3, sticky = W)
room_label.grid(row = 1, column = 1, sticky = W)
room_value.grid(row = 1, column = 2, sticky = W)
room_desc_label.grid(row = 2, column = 1, sticky = W)
room_desc_text.grid(row = 2, column = 2, sticky = W)

select_frame.grid(row = 2, column = 1)
players_label.grid(row = 1, column = 1, sticky = W)
players.grid(row = 2, column = 1)
monsters_label.grid(row = 3, column = 1, sticky = W)
monsters.grid(row = 4, column = 1)
connections_label.grid(row = 5, column = 1, sticky = W)
connections.grid(row = 6, column = 1)

chat_frame.grid(row = 2, column = 2)
text.grid(row = 1, column = 2)
input_field.grid(row = 2, column = 2, sticky = W)

right_frame.grid(row = 2, column = 3)

stats_frame.grid(row = 1, column = 1)
name_label.grid(row = 1, column = 1, sticky = W)
attack_label.grid(row = 2, column = 1, sticky = W)
defense_label.grid(row = 3, column = 1, sticky = W)
regen_label.grid(row = 4, column = 1, sticky = W)
health_label.grid(row = 5, column = 1, sticky = W)
gold_label.grid(row = 6, column = 1, sticky = W)
alive_label.grid(row = 7, column = 1, sticky = W)
fight_label.grid(row = 8, column = 1, sticky = W)

name_value.grid(row = 1, column = 2, sticky = W)
attack_value.grid(row = 2, column = 2, sticky = W)
defense_value.grid(row = 3, column = 2, sticky = W)
regen_value.grid(row = 4, column = 2, sticky = W)
health_value.grid(row = 5, column = 2, sticky = W)
gold_value.grid(row = 6, column = 2, sticky = W)
alive_value.grid(row = 7, column = 2, sticky = W)
fight_value.grid(row = 8, column = 2, sticky = W)

button_frame.grid(row = 2, column = 1)
join_button.grid(row = 1, column = 1)
start_button.grid(row = 2, column = 1)
room_button.grid(row = 3, column = 1)
fight_button.grid(row = 4, column = 1)
pvp_fight_button.grid(row = 5, column = 1)
loot_button.grid(row = 6, column = 1)
leave_button.grid(row = 7, column = 1)


### Key Bindings ###
input_field.bind("<Return>", enter_pressed)

console('Welcome! Enter a name and click JOIN')


### App Loop ###

def recv_loop():
    global exit_flag, players_dict, monsters_dict, connections_list
    while ptc.conn.connected:
        print('Waiting for message')
        message = ptc.decode()
        if message:
            mes_type = message['type']
            if mes_type == 1:
                if 'recipient' not in message:
                    console(message['text'], sender = message['sender'])
                else:
                    console(message['text'], sender = message['sender'], level = 4)
            elif mes_type == 7:
                text = f"Received Error: {message['code']}; {message['text']}"
                console(text, sender = 'Server', level = 3)
            elif mes_type == 8:
                text = f"Action Accepted: {message['code']}"
                console(text, sender = 'Server', level = 1)
                if int(message['code']) == 12: break
            elif mes_type == 9:
                current_room['name'] = message['name']
                current_room['number'] = message['room']
                current_room['desc'] = message['text']
                text = f"Current Room: {message['name']}({message['room']}); {message['text']}"
                console(text, sender = 'Server')
                update_room()
            elif mes_type == 10:
                message['flags'] = f"{message['flags']:08b}"
                message['alive'] = True if int(message['flags'][0]) else False
                message['join'] = True if int(message['flags'][1]) else False
                if int(message['flags'][2]):
                    monsters_dict[message['name']] = message
                    update_monsters()
                else:
                    if message['name'] == character_dict['name']:
                        for key, value in message.items():
                            character_dict[key] = value
                        update_stats(message)
                    else:
                        players_dict[message['name']] = message
                        update_players()
            elif mes_type == 11:
                console(message['text'], sender = 'Server')
                text = f"Initial Points: {message['points']}, Stat Limit: {message['limit']}"
                console(text, sender = 'Server')
            elif mes_type == 13:
                # text = f"Connecting Room: {message['name']}({message['room']}); {message['text']}"
                # console(text, sender = 'Server')
                connection = (message['name'], message['room'])
                if connection not in connections_list:
                    connections_list.append(connection)
                    update_connections()
            elif mes_type == 14:
                text = f"LURK Version: {message['major']}.{message['minor']};\tExtensions: {message['text']}"
                console(text, sender = 'Server', level = 1)
    console('You have left the game!')
    exit_flag.set(True)

recv_thread = threading.Thread(target = recv_loop)

window.mainloop()

leave()
