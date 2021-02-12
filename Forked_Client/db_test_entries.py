from models import Monster, Room, Connection, Loot

main_room = Room('Living Room', 'Mr. Rowanitz trophy game mounts and obsurdly valuable furniture and coverings fill the sprawling lodge main-room.')
hallway = Room('Hallway', 'Connects the main-room to deeper parts of the lodge.')

connection1 = Connection(1, 2)
connection2 = Connection(2, 1)

Monster('Chuck', 20, 20, 20, 100, 100, 2, 'Mostly harmless, practice mild caution.')