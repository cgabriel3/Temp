import time
from phabricator import Phabricator
from tapd import Tapd
import configparser
import argparse
import re
import logging
import datetime
import os
import json
from datetime import datetime, time, timedelta
import html2text
from bs4 import BeautifulSoup

directory = os.path.dirname(__file__)

# Tapd Priority to Phabricator Priority
tapd_story_priority_to_phabricator_task_priority = {
  "Nice To Have": 'wish',
  "Low": 'low',
  "Middle": 'normal',
  "High": 'high'
}

tapd_task_priority_to_phabricator_task_priority = {
  "1": 'wish',
  "2": 'low',
  "3": 'normal',
  "4": 'high'
}

tapd_story_status_to_phabricator_status = {
  'Assess Finished': "resolved",
  'Developing': "open",
  "Suspended": "open",
  "Exceptionally Terminated": "invalid"
}

tapd_task_status_to_phabricator_status = {
  "done": "resolved",
  "progressing": "open",
  "open": "open",
}


def setup_logging():
  # Configure the logging module
  timestamp = datetime.now().strftime('%d-%m-%Y')
  sync_tasks_log_file = f'{directory}/../../sync_tasks_log_{timestamp}.log'

  # Configure the logger
  logging.basicConfig(
    filename=sync_tasks_log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
  )


def get_env(env):
  if not env:
    env = 'prod'
  return f'{directory}/config.{env}.ini'


def get_creator_api_token(username_to_phabricator_api_token_map, creator, default_api_token):
  return username_to_phabricator_api_token_map.get(creator, default_api_token)


def remove_html_tags(text):
  return re.sub(r'<.*?>', '', text) if text else ""


def extract_id_from_text(text):
  # Get the ID at the end of the  URL
  match = re.search(r'/(\d+)$', text)
  if match:
    return match.group(1)
  return None


def extract_tapd_story_id_from_text(text):
  if '/stories/view/' in text:
    return extract_id_from_text(text)


def extract_tapd_task_id_from_text(text):
  if '/tasks/view/' in text:
    return extract_id_from_text(text)


def extract_tapd_images_from_description(img_tags):
  src_values = [img['src'] for img in img_tags]
  return {'src_values': src_values, 'img_tags': img_tags}


def format_task_description(task_description, tapd_story_url, tapd, phabricator):
  if task_description is None:
    return ""
  config = html2text.HTML2Text()
  config.body_width = 0
  config.images_as_html = True
  task_description = config.handle(task_description)
  task_description = task_description.replace(r'\.', '.').replace(' />', '/>')
  soup = BeautifulSoup(task_description, 'html.parser')
  img_tags = soup.find_all('img')
  images = extract_tapd_images_from_description(img_tags)

  for index, image in enumerate(images['src_values']):
    res = tapd.get_images(image)
    file_info = phabricator.upload_file(res)
    if file_info:
      file_object = phabricator.get_file(file_info)
      task_description = task_description.replace(str(img_tags[index]).replace('"', "'"), "{" + file_object + "}")

  formatted_description = f'{task_description}\n\nTAPD Story Link: {tapd_story_url}'
  return formatted_description


def format_sub_task_description(task_description, tapd_task_id, workspace_id):
  task_description = re.sub(r'<.*?>', '', task_description) if task_description else ""
  tapd_task_url = "https://www.tapd.cn/" + workspace_id + "/prong/tasks/view/" + tapd_task_id
  formatted_description = f'{task_description}\n\nTAPD Task Link: {tapd_task_url}'
  return formatted_description


def format_phabricator_comment(description):
  return f'{remove_html_tags(description)}'


def create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list):
  tapd_story_id_to_phabricator_task = {}
  tapd_task_id_to_phabricator_task = {}
  for task in phabricator_task_list:
    tapd_story_id = extract_tapd_story_id_from_text(task['fields']['description']['raw'])
    tapd_task_id = extract_tapd_task_id_from_text(task['fields']['description']['raw'])
    if tapd_story_id is not None or tapd_task_id is not None:
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

      phabricator_task = {
        'id': task['id'],
        'phid': task['phid'],
        'title': task_fields['name'],
        'description': task_fields['description']['raw'],
        'owner': task_fields['ownerPHID'],
        'priority': task_fields['priority']['name'].lower(),
        'developers': task_developer,
        'testers': task_tester,
        'column': task_column_id,
        'status': task_fields['status']['value']
      }

      if tapd_story_id is not None:
        tapd_story_id_to_phabricator_task[tapd_story_id] = phabricator_task

      if tapd_task_id is not None:
        tapd_task_id_to_phabricator_task[tapd_task_id] = phabricator_task

  return tapd_story_id_to_phabricator_task, tapd_task_id_to_phabricator_task


def split_user_list(user_list):
  return [user for user in user_list.split(";") if user]


def format_create_task_fields(phabricator, tapd_story_fields, tapd):
  sync_description = format_task_description(
    tapd_story_fields['description'],
    tapd_story_fields['url'],
    tapd,
    phabricator
  )

  phabricator_owner_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['owner']))

  phabricator_developer_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['developer']))

  phabricator_tester_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['qa']))

  sync_fields = {
    'title': tapd_story_fields['name'],
    'description': sync_description,
    'owner': phabricator_owner_id_list,
    'developers': phabricator_developer_id_list,
    'testers': phabricator_tester_id_list,
    'column': tapd_story_fields['category'],
    'status': tapd_story_status_to_phabricator_status.get(tapd_story_fields['status'], "open"),
    'priority': tapd_story_priority_to_phabricator_task_priority.get(tapd_story_fields['priority'], "normal")
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


def format_create_sub_task_fields(phabricator, tapd_task):
  task_owner = phabricator.get_user_id_list(split_user_list(tapd_task['owner']))
  tapd_task = {
    'title': tapd_task['name'],
    'description': format_sub_task_description(tapd_task['description'], tapd_task['id'], tapd_task['workspace_id']),
    'owner': task_owner,
    'status': tapd_task_status_to_phabricator_status.get(tapd_task['status'], "open"),
    'priority': tapd_task_priority_to_phabricator_task_priority.get(tapd_task['priority'], "normal"),
  }
  return tapd_task


def format_update_sub_task_fields(tapd_task_fields, phabricator_task_fields):
  update_fields = {
    'task_id': phabricator_task_fields['id']
  }
  for field, value in tapd_task_fields.items():
    if phabricator_task_fields[field] != value:
      update_fields[field] = value
  return update_fields


def filter_task(task):
  start_of_the_previous_day = datetime.combine(datetime.now() - timedelta(1), time.min)
  story_time_format = '%Y-%m-%d %H:%M:%S'
  story_modified_time = datetime.strptime(task['Task']['modified'], story_time_format)
  if story_modified_time > start_of_the_previous_day:
    return True
  else:
    return False


def filtered_tasks(tasks):
  filtered_task_list = filter(lambda x: filter_task(x), tasks)
  return filtered_task_list


def sync_tapd_stories_phabricator_tasks(env):
  logging.info("Sync Task Start")
  config = configparser.ConfigParser()
  config.read(env)

  phabricator = Phabricator(config)
  tapd = Tapd(config)

  username_to_phabricator_api_token_map = json.loads(config['phabricator']['api_token_map'])
  default_api_token = config['phabricator']['api_token']

  tapd_story_list = tapd.get_stories()
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map, task_id_to_phabricator_task_map = create_tapd_story_and_tapd_task_to_phabricator_task_mapping(
    phabricator_task_list)

  for story in tapd_story_list:
    story_id = story['id']
    phabricator_task_fields = story_id_to_phabricator_task_map.get(story_id)
    sync_fields = format_create_task_fields(phabricator, story, tapd)

    if tapd_story_status_to_phabricator_status.get(story['status']) == "resolved" and phabricator_task_fields is None:
      continue

    if phabricator_task_fields:
      sync_fields = format_update_task_fields(sync_fields, phabricator_task_fields)

    sync_fields["creator_api_token"] = get_creator_api_token(username_to_phabricator_api_token_map, story["creator"], default_api_token)
    task_response = phabricator.create_update_task(sync_fields)
    if task_response and phabricator_task_fields is None:
      update_story_fields = {
        'task_url': "https://code.yangqianguan.com/T" + str(task_response['object']['id']),
        'story_id': story['id']
      }
      tapd.edit_story(update_story_fields)

  story_comment_list = tapd.get_comments()
  for comment in story_comment_list:
    story_id = comment['entryId']
    phabricator_task = story_id_to_phabricator_task_map.get(story_id)

    if phabricator_task:
      phabricator_task_id = phabricator_task['id']
      formatted_phabricator_comment = format_phabricator_comment(comment['description'])
      comment_fields = {
        'task_id': phabricator_task_id,
        'comment': formatted_phabricator_comment,
        'commentator_api_token': get_creator_api_token(username_to_phabricator_api_token_map, comment["author"], default_api_token)
      }
      phabricator.create_comment(comment_fields)

  tapd_task_list = tapd.get_task()
  filtered_tapd_task_list = filtered_tasks(tapd_task_list)
  for tapd_task in filtered_tapd_task_list:
    tapd_task = tapd_task['Task']
    phabricator_parent_task = story_id_to_phabricator_task_map.get(tapd_task['story_id'])

    if phabricator_parent_task is None:
      continue

    phabricator_task_fields = task_id_to_phabricator_task_map.get(tapd_task['id'])
    sync_fields = format_create_sub_task_fields(phabricator, tapd_task)
    if phabricator_task_fields is not None:
      sync_fields = format_update_sub_task_fields(sync_fields, phabricator_task_fields)
    sync_fields['creator_api_token'] = get_creator_api_token(username_to_phabricator_api_token_map, tapd_task['creator'], default_api_token)
    sync_fields['parent'] = phabricator_parent_task['phid']
    phabricator.create_update_subtask(sync_fields)
  logging.info("Sync Task finish")


def main():
  parser = argparse.ArgumentParser(description='Sync Task Script')
  parser.add_argument('--env', help='Environment')
  args = parser.parse_args()
  setup_logging()
  sync_tapd_stories_phabricator_tasks(get_env(args.env))


main()
