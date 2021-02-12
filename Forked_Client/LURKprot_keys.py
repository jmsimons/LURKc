
error_key = {
    0: 'Other',
    1: 'Bad Room Number',
    2: 'Name Already Taken',
    3: 'No Monster',
    4: 'Bad Stats',
    5: 'Player Not Ready',
    6: 'No Target',
    7: 'No Fight',
    8: 'No PVP Fight'
}

message_types = {
    1: 'Chat', # <->
    2: 'Change Room', # <-
    3: 'Fight', # <-
    4: 'PVP Fight', # <-
    5: 'Loot', # <-
    6: 'Start', # <-
    7: 'Error', # ->
    8: 'Action Accepted', # ->
    9: 'Current Room', # ->
    10: 'Character', # <->
    11: 'Game', # ->
    12: 'Leave Game', # <-
    13: 'Connecting Room', # ->
    14: 'LURK Version' # ->
}

message_key = {
    1: {'order': ('length', 'recipient', 'sender', 'text'),
        'length': (2, '<H'),
        'recipient': (32, '<32B'),
        'sender': (32, '<32B'),
        'text': (0, '<{}B')},
    2: {'order': ('room', ),
        'room': (2, '<H'),},
    3: {'order': ()},
    4: {'order': ('name', ),
        'name': (32, '<32B')},
    5: {'order': ('name', ),
        'name': (32, '<32B')},
    6: {'order': ()},
    7: {'order': ('code', 'length', 'text'),
        'code': (1, '<B'),
        'length': (2, '<H'),
        'text': (0, '<{}B')},
    8: {'order': ('code', ),
        'code': (1, '<B')},
    9: {'order': ('room', 'name', 'length', 'text'),
        'room': (2, '<H'),
        'name': (32, '<32B'),
        'length': (2, '<H'),
        'text': (0, '<{}B')},
    10: {'order': ('name', 'flags', 'attack', 'defense', 'regen', 'health', 'gold', 'room', 'length', 'text'),
        'name': (32, '<32B'),
        'flags': (1, '<B'),
        'attack': (2, '<H'),
        'defense': (2, '<H'),
        'regen': (2, '<H'),
        'health': (2, '<h'),
        'gold': (2, '<H'),
        'room': (2, '<H'),
        'length': (2, '<H'),
        'text': (0, '<{}B')},
    11: {'order': ('points', 'limit', 'length', 'text'),
        'points': (2, '<H'),
        'limit': (2, '<H'),
        'length': (2, '<H'),
        'text': (0, '<{}B')},
    12: {'order': ()},
    13: {'order': ('room', 'name', 'length', 'text'),
        'room': (2, '<H'),
        'name': (32, '<32B'),
        'length': (2, '<H'),
        'text': (0, '<{}B')},
    14: {'order': ('major', 'minor', 'length', 'text'),
        'major': (1, '<B'),
        'minor': (1, '<B'),
        'length': (2, '<H'),
        'text': (0, '<{}B')}
}