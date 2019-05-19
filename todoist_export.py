# Todoist Export for Python 3

from todoist.api import TodoistAPI
import pandas as pd
import json

# Authentification
with open("credentials.json", "r") as file:
    credentials = json.load(file)
    todoist_cr = credentials['todoist']
    TOKEN = todoist_cr['TOKEN']

api = TodoistAPI(TOKEN)

# Intitial Sync
api.sync()

# User Info
user = api.state['user']
user_name = user['full_name']


#  User Projects

user_projects = api.state['projects']
projects = pd.DataFrame([p.data for p in user_projects])
print("Creating Export of Current Todoist Projects")
pd.write_csv("data/todoist-projects.csv")
    
# User Stats

stats = api.completed.get_stats()

user_completed_count = stats['completed_count']
user_completed_stats = stats['completed_count']

# Export Completed Todoist Items

def get_completed_todoist_items():

    # create df from initial 50 completed tasks

    print("Collecting Initial 50 Completed Todoist Tasks...")
    temp_tasks_dict = (api.completed.get_all(limit=50))
    past_tasks = pd.DataFrame.from_dict(temp_tasks_dict['items'])
    # get the remaining items
    pager = list(range(50,user_completed_count,50))
    for count, item in enumerate(pager):
        tmp_tasks = (api.completed.get_all(limit=50, offset=item))
        tmp_tasks_df = pd.DataFrame.from_dict(tmp_tasks['items'])
        past_tasks = pd.concat([past_tasks, tmp_tasks_df])
        print("Collecting Additional Todoist Tasks " + str(item) + " of " + str(user_completed_count))
    # save to CSV
    print("...Generating CSV Export")
    past_tasks.to_csv("data/todost-raw-tasks-completed.csv", index=False)

get_completed_todoist_items()
past_tasks = pd.read_csv("data/todost-raw-tasks-completed.csv")

# past_tasks.head()

# generated count 
collected_total = len(past_tasks)

# Does our collected total tasks match stat of completed count on user
print("Does our export of past completed tasks match user stats of completed task count?")
print(collected_total == user_completed_count)

past_tasks['project_id'] = past_tasks.project_id.astype('category')

# Extract all project ids used on tasks
project_ids = past_tasks.project_id.unique()

# get project info from Todoist API
def get_todoist_project_name(project_id):
    item = api.projects.get_by_id(project_id)
    if item: 
        try:
            return item['name']
        except:
            return item['project']['name']

# Get Info on All User Projects
project_names = []
for i in project_ids:
    project_names.append(get_todoist_project_name(i))

# Probably a more effecient way to do this
project_lookup = lambda x: get_todoist_project_name(x)
print("Assigning Project Name on Tasks...")
past_tasks['project_name'] = past_tasks['project_id'].apply(project_lookup)

# Add Day of Week Completed

past_tasks['completed_date'] = pd.to_datetime(past_tasks['completed_date'])
past_tasks['dow'] = past_tasks['completed_date'].dt.weekday
past_tasks['day_of_week'] = past_tasks['completed_date'].dt.weekday_name

# save to CSV
past_tasks.to_csv("data/todost-tasks-completed.csv", index=False)

items_df = pd.DataFrame(i.data for i in api.state['items'])
items_df.to_csv('data/current-tasks-raw.csv')


# Add project name to df

current_tasks = items_df.merge(
    projects[['id', 'name']],
    left_on='project_id',
    right_on='id'
)


# Add Day of Week Added

current_tasks['date_added'] = pd.to_datetime(current_tasks['date_added'])
current_tasks['dow_added'] = current_tasks['date_added'].dt.weekday
current_tasks['day_of_week_added'] = current_tasks['date_added'].dt.weekday_name

print("Generating Processed Export of Current Todoist Tasks")
current_tasks.to_csv('data/current-tasks.csv', index=False)
