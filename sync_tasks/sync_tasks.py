import time
from phabricator import Phabricator
from tapd import Tapd
import configparser
import argparse
import re
import logging
import datetime

# Tapd Priority to Phabricator Priority
tapd_to_phabricator_task_priority = {
  "Nice To Have": 'wish',
  "Low": 'low',
  "Middle": 'normal',
  "High": 'high'
}

tapd_to_phabricator_status = {
  'Assess Finished': "resolved",
  'Developing': "open",
  "Suspended": "open",
  "Exceptionally Terminated": "invalid"
}


def setup_logging():
  # Configure the logging module
  timestamp = datetime.datetime.now().strftime('%d-%m-%Y')
  sync_tasks_log_file = f'../../sync_tasks_log_{timestamp}.log'

  # Configure the logger
  logging.basicConfig(
    filename=sync_tasks_log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
  )


def get_env(env):
  if not env:
    env = 'prod'
  return f'config.{env}.ini'


def remove_html_tags(text):
  return re.sub(r'<.*?>', '', text) if text else ""


def extract_tapd_story_id_from_text(text):
  match = re.search(r'/(\d+)$', text)
  if match:
    return match.group(1)
  return None


def format_task_description(task_description, tapd_story_url):
  task_description = re.sub(r'<.*?>', '', task_description) if task_description else ""
  formatted_description = f'{task_description}\n\nTAPD Story Link: {tapd_story_url}'
  return formatted_description


def format_phabricator_comment(author, description):
  return f'By {author} from TAPD:\n {remove_html_tags(description)}'


def create_tapd_story_to_phabricator_task_mapping(phabricator_task_list):
  tapd_story_url_to_phabricator_task = {}
  for task in phabricator_task_list:
    tapd_story_id = extract_tapd_story_id_from_text(task['fields']['description']['raw'])
    if tapd_story_id is not None:
      task_fields = task['fields']

      task_column = task['attachments']['columns']['boards']
      board_data = list(task_column.values())[0]
      task_column_id = board_data['columns'][0]['name']

      task_developer = []
      if task_fields['custom.maniphest:developers']:
        task_developer = task_fields['custom.maniphest:developers']

      task_tester = []
      if task_fields['custom.maniphest:testers']:
        task_tester = task_fields['custom.maniphest:testers']

      tapd_story_url_to_phabricator_task[tapd_story_id] = {
        'id': task['id'],
        'title': task_fields['name'],
        'description': task_fields['description']['raw'],
        'owner': task_fields['ownerPHID'],
        'priority': task_fields['priority']['name'].lower(),
        'developers': task_developer,
        'testers': task_tester,
        'column': task_column_id,
        'status': task_fields['status']['value']
      }
  return tapd_story_url_to_phabricator_task


def format_create_task_fields(phabricator, tapd_story_fields):
  sync_description = format_task_description(tapd_story_fields['description'], tapd_story_fields['url'])

  tapd_owner_list = [owner for owner in tapd_story_fields['owner'].split(";") if owner]
  phabricator_owner_id_list = phabricator.get_user_id_list(tapd_owner_list)

  tapd_developer_list = [developer for developer in tapd_story_fields['developer'].split(";") if developer]
  phabricator_developer_id_list = phabricator.get_user_id_list(tapd_developer_list)

  tapd_tester_list = [tester for tester in tapd_story_fields['qa'].split(";") if tester]
  phabricator_tester_id_list = phabricator.get_user_id_list(tapd_tester_list)

  phabricator_priority = tapd_to_phabricator_task_priority.get(tapd_story_fields['priority'], tapd_to_phabricator_task_priority['Middle'])

  sync_fields = {
    'title': tapd_story_fields['name'],
    'description': sync_description,
    'owner': phabricator_owner_id_list,
    'developers': phabricator_developer_id_list,
    'testers': phabricator_tester_id_list,
    'column': tapd_story_fields['category'],
    'status': tapd_to_phabricator_status.get(tapd_story_fields['status'], 'open'),
    'priority': phabricator_priority
  }
  if tapd_story_fields.get('phabricator_task_id'):
    sync_fields['task_id'] = tapd_story_fields['phabricator_task_id']

  return sync_fields


def format_update_task_fields(tapd_story_fields, phabricator_task_fields):
  update_fields = {
    'task_id': phabricator_task_fields['id']
  }
  for field, value in tapd_story_fields.items():
    if phabricator_task_fields[field] != value:
      update_fields[field] = value
  return update_fields


def sync_tapd_stories_phabricator_tasks(env):
  config = configparser.ConfigParser()
  config.read(env)

  phabricator = Phabricator(config)
  tapd = Tapd(config)

  tapd_story_list = tapd.get_stories()
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map = create_tapd_story_to_phabricator_task_mapping(phabricator_task_list)

  for story in tapd_story_list:
    story_id = story['id']
    phabricator_task_fields = story_id_to_phabricator_task_map.get(story_id)
    sync_fields = format_create_task_fields(phabricator, story)
    if phabricator_task_fields:
      sync_fields = format_update_task_fields(sync_fields, phabricator_task_fields)

    phabricator.create_update_task(sync_fields)

  story_comment_list = tapd.get_comments()
  for comment in story_comment_list:
    story_id = comment['entryId']
    phabricator_task = story_id_to_phabricator_task_map.get(story_id)
    if phabricator_task:
      phabricator_task_id = phabricator_task['id']
      formatted_phabricator_comment = format_phabricator_comment(comment['author'], comment['description'])
      comment_fields = {
        'task_id': phabricator_task_id,
        'comment': formatted_phabricator_comment
      }
      phabricator.create_comment(comment_fields)


def main():
  parser = argparse.ArgumentParser(description='Sync Task Script')
  parser.add_argument('--env', help='Environment')
  args = parser.parse_args()

  setup_logging()
  sync_tapd_stories_phabricator_tasks(get_env(args.env))


main()
