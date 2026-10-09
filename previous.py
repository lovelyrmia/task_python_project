import datetime

users = {
 'alice': {'quota': 3, 'executed': 0},
 'bob': {'quota': 5, 'executed': 0}
}

tasks = [
 {'user': 'alice', 'time': '12:00', 'action': 'sync', 'target': '/data/x'},
 {'user': 'bob', 'time': '12:00', 'action': 'backup', 'target': '/srv/y'},
 {'user': 'alice', 'time': '12:00', 'action': 'delete', 'target': '/tmp/z'},
]

def run():
 now = datetime.datetime.now().strftime('%H:%M')
 for task in tasks:
     if task['time'] == now:
         user = task['user']
         if users[user]['executed'] >= users[user]['quota']:
             print(f"{user} has exceeded quota.")
             continue
         print(f"Executing {task['action']} on {task['target']} for {user}")
         users[user]['executed'] += 1