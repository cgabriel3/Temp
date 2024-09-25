import time as t
from phabricator import Phabricator
from tapd import Tapd
import configparser
import argparse
import re
import logging
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
  "Assess Finished": "open",
  "Developing": "open",
  "Suspended": "open",
  "Exceptionally Terminated": "invalid",
  "In Production": "resolved",
  "Validation Finished": "resolved"
}

tapd_task_status_to_phabricator_status = {
  "done": "resolved",
  "progressing": "open",
  "open": "open",
}


def setup_logging():
  # Configure the logging module
  timestamp = datetime.now().strftime('%d-%m-%Y')
  sync_tasks_log_file = f'{directory}/../script_logs/sync_tasks_log_{timestamp}.log'

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


def insert_phabricator_image_to_task_description(tapd, phabricator, images, task_description, img_tags):
  for index, image in enumerate(images['src_values']):
    for i in range(2):
      try:
        logging.info(f"Downloading Image {index} from TAPD")
        res = tapd.get_images(image)
        logging.info(f"Uploading Image {index} to Phabricator")
        file_info = phabricator.upload_file(res)
        if file_info:
          logging.info(f"Inserting Image {index} to Task Description")
          file_object = phabricator.get_file(file_info)
          task_description = task_description.replace(str(img_tags[index]).replace('"', "'"), "{" + file_object + "}")
          break
      except Exception as e:
        if i < 2:
          logging.info(f"Retrying insert image for the {i + 1} time...")
          t.sleep(tapd.sleep)  # Wait before retrying
        else:
          logging.error(f'Failed to insert image. Error: {e}')

  return task_description


def format_task_description(task_description, tapd_story_url, tapd, phabricator):
  if task_description is None:
    return f"TAPD Story Link: {tapd_story_url}"

  config = html2text.HTML2Text()
  config.body_width = 0
  config.images_as_html = True
  task_description = config.handle(task_description)
  task_description = task_description.replace(r'\.', '.').replace(' />', '/>')
  soup = BeautifulSoup(task_description, 'html.parser')
  img_tags = soup.find_all('img')
  images = extract_tapd_images_from_description(img_tags)
  task_description = insert_phabricator_image_to_task_description(tapd, phabricator, images, task_description, img_tags)

  formatted_description = f'{task_description}\n\nTAPD Story Link: {tapd_story_url}'
  return formatted_description


def format_sub_task_description(task_description, tapd_task_url):
  task_description = re.sub(r'<.*?>', '', task_description) if task_description else ""
  formatted_description = f'{task_description}\n\nTAPD Task Link: {tapd_task_url}'
  return formatted_description


def format_phabricator_comment(description):
  return f'{remove_html_tags(description)}'


def create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list, tapd_id_to_story_list, tapd_id_to_sub_story_list):
  tapd_story_id_to_phabricator_task = {}
  tapd_task_id_to_phabricator_task = {}
  for task in phabricator_task_list:
    tapd_id = extract_tapd_story_id_from_text(task['fields']['description']['raw'])
    tapd_story_id = None
    tapd_task_id = None
    if tapd_id_to_story_list.get(tapd_id) is not None:
      tapd_story_id = tapd_id

    if tapd_id_to_sub_story_list.get(tapd_id):
      tapd_task_id = tapd_id

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
  tapd_story_id = tapd_story_fields['id']
  tapd_category_id = tapd_story_fields['category_id']
  tapd_story_url = tapd.generate_story_url(tapd_story_id)
  sync_description = format_task_description(
    tapd_story_fields['description'],
    tapd_story_url,
    tapd,
    phabricator
  )

  phabricator_owner_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['owner']))

  sync_fields = {
    'title': tapd_story_fields['name'],
    'description': sync_description,
    'owner': phabricator_owner_id_list,
    'column': tapd.get_category_name_from_category_id(tapd_category_id),
    'status': tapd_story_status_to_phabricator_status.get(tapd_story_fields['status'], "open"),
    'priority': tapd_story_priority_to_phabricator_task_priority.get(tapd_story_fields['priority'], "normal")
  }

  if tapd.is_not_doc_template(tapd_story_id):
    phabricator_developer_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['developer']))
    phabricator_tester_id_list = phabricator.get_user_id_list(split_user_list(tapd_story_fields['custom_field_three']))
    sync_fields['developers'] = phabricator_developer_id_list
    sync_fields['testers']: phabricator_tester_id_list

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


def format_create_sub_task_fields(phabricator, tapd_task, phabricator_parent_task, tapd):
  task_owner = phabricator.get_user_id_list(split_user_list(tapd_task['owner']))
  tapd_task_url = tapd.generate_story_url(tapd_task['id'])
  tapd_task = {
    'title': tapd_task['name'],
    'description': format_sub_task_description(tapd_task['description'], tapd_task_url),
    'owner': task_owner,
    'status': tapd_task_status_to_phabricator_status.get(tapd_task['status'], "open"),
    'priority': tapd_task_priority_to_phabricator_task_priority.get(tapd_task['priority'], "normal"),
    'column': phabricator_parent_task['column'],
    'parent': phabricator_parent_task['phid']
  }
  return tapd_task


def format_update_sub_task_fields(tapd_task_fields, phabricator_task_fields):
  update_fields = {
    'task_id': phabricator_task_fields['id']
  }
  tapd_task_fields.pop('parent')
  for field, value in tapd_task_fields.items():
    if phabricator_task_fields[field] != value:
      update_fields[field] = value
  return update_fields


def filter_updated_story(story):
  story_time_format = '%Y-%m-%d %H:%M:%S'
  story_modified_time = datetime.strptime(story['Story']['modified'], story_time_format)
  if story_modified_time < get_date_time_end_of_previous_day():
    return True
  else:
    return False


def extract_tapd_story_and_sub_story(tapd_stories):
  tapd_story_list = []
  tapd_sub_story_list = []

  for story in tapd_stories:
    if story['Story']['ancestor_id'] == story['Story']['id']:
      tapd_story_list.append(story)

    else:
      tapd_sub_story_list.append(story)

  return tapd_story_list, tapd_sub_story_list


def get_updated_story(stories):
  updated_story_list = filter(lambda x: filter_updated_story(x), stories)
  return list(updated_story_list)


def invalidate_task(phabricator_task):
  task = {
    'task_id': phabricator_task['phid'],
    'status': 'invalid'
  }
  return task


def extract_tapd_story_id(tapd_story_list):
  return [story["Story"]["id"] for story in tapd_story_list]


def extract_tapd_task_id(tapd_task_list):
  return [task["Task"]["id"] for task in tapd_task_list]


def get_date_time_start_of_previous_day():
  now = datetime.now() - timedelta(days=1)
  start_of_day = datetime(now.year, now.month, now.day)
  return start_of_day.strftime("%Y-%m-%d %H:%M:%S")


def get_date_time_end_of_previous_day():
  now = datetime.now() - timedelta(days=1)
  end_of_day = datetime.combine(now.date(), time.max)
  return end_of_day


def create_story_id_to_story_map(tapd_story_list):
  return {item['Story']['id']: item for item in tapd_story_list}


def update_story_diff(tapd, tapd_story, tapd_sub_story):
  story_diff_list_str = tapd_story.get("custom_field_six")
  story_diff_set = set()
  original_story_diff_set = set()
  if story_diff_list_str is not None:
    diff_list = story_diff_list_str.split()
    story_diff_set = set(diff_list)
    original_story_diff_set = set(diff_list)

  sub_story_diff_list_str = tapd_sub_story.get("custom_field_six")
  if sub_story_diff_list_str is None:
    return

  sub_story_diff_set = set(sub_story_diff_list_str.split())
  combined_diff_set = sub_story_diff_set.union(story_diff_set)

  if story_diff_set == original_story_diff_set:
    return
  
  update_story_diff_fields = {
    "story_id": tapd_story['id'],
    "story_diff": " ".join(combined_diff_set)
  }
  tapd.edit_story(update_story_diff_fields)
  return


def sync_tapd_stories_phabricator_tasks(env):
  logging.info("Sync Task Start")
  config = configparser.ConfigParser()
  config.read(env)

  phabricator = Phabricator(config)
  tapd = Tapd(config)

  username_to_phabricator_api_token_map = json.loads(config['phabricator']['api_token_map'])
  default_api_token = config['phabricator']['api_token']
  tapd_all_story_list = tapd.get_all_stories(get_date_time_start_of_previous_day())
  tapd_story_list, tapd_sub_story_list = extract_tapd_story_and_sub_story(tapd_all_story_list)
  tapd_story_id_to_story_map = create_story_id_to_story_map(tapd_story_list)
  tapd_sub_story_id_to_sub_story_map = create_story_id_to_story_map(tapd_sub_story_list)
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map, task_id_to_phabricator_task_map = create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list, tapd_story_id_to_story_map, tapd_sub_story_id_to_sub_story_map)

  for story in tapd_story_list:
    story_content = story['Story']
    story_id = story_content['id']
    phabricator_task_fields = story_id_to_phabricator_task_map.get(story_id)
    sync_fields = format_create_task_fields(phabricator, story_content, tapd)

    if tapd_story_status_to_phabricator_status.get(story_content['status']) == "resolved" and phabricator_task_fields is None:
      continue

    if phabricator_task_fields:
      sync_fields = format_update_task_fields(sync_fields, phabricator_task_fields)

    sync_fields["creator_api_token"] = get_creator_api_token(username_to_phabricator_api_token_map, story_content["creator"], default_api_token)
    task_response = phabricator.create_update_task(sync_fields)
    if task_response and phabricator_task_fields is None:
      update_story_fields = {
        'task_url': "https://code.yangqianguan.com/T" + str(task_response['object']['id']),
        'story_id': story_content['id']
      }
      tapd.edit_story(update_story_fields)

  story_comment_list = tapd.get_comments()
  if len(story_comment_list) == 0:
    logging.info("There are no comments on TAPD today")

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

  for tapd_sub_story in tapd_sub_story_list:
    tapd_sub_story_content = tapd_sub_story['Story']
    phabricator_parent_task = story_id_to_phabricator_task_map.get(tapd_sub_story_content['ancestor_id'])

    if phabricator_parent_task is None:
      continue

    phabricator_task_fields = task_id_to_phabricator_task_map.get(tapd_sub_story_content['id'])
    sync_fields = format_create_sub_task_fields(phabricator, tapd_sub_story_content, phabricator_parent_task, tapd)
    if phabricator_task_fields is not None:
      sync_fields = format_update_sub_task_fields(sync_fields, phabricator_task_fields)
      
    if tapd_sub_story['custom_field_six'] is not None:
      tapd_story = tapd_story_id_to_story_map.get(tapd_sub_story_content['ancestor_id'])
      update_story_diff(tapd, tapd_story, tapd_sub_story_content)

    sync_fields['creator_api_token'] = get_creator_api_token(username_to_phabricator_api_token_map, tapd_sub_story_content['creator'], default_api_token)
    phabricator.create_update_subtask(sync_fields)

  # Check if there are any invalidated task on Monday
  if datetime.today().weekday() == 0:
    invalidated_tasks = []
    invalidated_subtasks = []
    tapd_all_story_list = tapd.get_all_stories()
    tapd_story_list, tapd_sub_story_list = extract_tapd_story_and_sub_story(tapd_all_story_list)
    # Invalidate Unused Tasks:
    tapd_story_id_set = set(extract_tapd_story_id(tapd_story_list))
    phabricator_story_id_set = set(story_id_to_phabricator_task_map.keys())
    difference = phabricator_story_id_set - tapd_story_id_set

    for tapd_story_id in difference:
      phabricator_task = story_id_to_phabricator_task_map.get(tapd_story_id)
      if phabricator_task is None:
        continue
      sync_fields = invalidate_task(phabricator_task)
      sync_fields['creator_api_token'] = get_creator_api_token(username_to_phabricator_api_token_map, phabricator_task['owner'], default_api_token)
      phabricator.create_update_task(sync_fields)
      invalidated_tasks.append(phabricator_task['id'])

    # Invalidate Unused Subtask
    tapd_task_id_set = set(extract_tapd_story_id(tapd_sub_story_list))
    phabricator_task_id_set = set(task_id_to_phabricator_task_map.keys())
    difference = phabricator_task_id_set - tapd_task_id_set

    for tapd_task_id in difference:
      phabricator_subtask = task_id_to_phabricator_task_map.get(tapd_task_id)
      if phabricator_subtask is None:
        continue
      sync_fields = invalidate_task(phabricator_subtask)
      sync_fields['creator_api_token'] = get_creator_api_token(username_to_phabricator_api_token_map, phabricator_subtask['owner'], default_api_token)
      phabricator.create_update_task(sync_fields)
      invalidated_subtasks.append(phabricator_subtask['id'])

    if len(invalidated_tasks) > 0:
      logging.info("Invalidated Tasks: ", invalidated_tasks)

    if len(invalidated_subtasks) > 0:
      logging.info("Invalidated Subtasks: ", invalidated_subtasks)

  logging.info("Sync Task finish")


def main():
  parser = argparse.ArgumentParser(description='Sync Task Script')
  parser.add_argument('--env', help='Environment')
  args = parser.parse_args()
  setup_logging()
  sync_tapd_stories_phabricator_tasks(get_env(args.env))


main()
