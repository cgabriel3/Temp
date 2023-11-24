import logging
import requests
import time


class Tapd:
  def __init__(self, config):
    section = "tapd"
    self.config = config
    self.api_url = config.get(section, 'api_url')
    self.project = config.get(section, 'project')
    self.workspace_id = config.get(section, 'workspace_id')
    self.max_retries = config.getint(section, 'max_retries')

  def get_stories(self):
    get_stories_api = f'api/tapd/external/story/getStoryBySource?source={self.project}'

    try:
      story_list = self.send_tapd_request_get(get_stories_api)
      return story_list
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')
      return []

  def get_comments(self):
    get_comments_api = f'api/tapd/external/comment/getCommentBySource?source={self.project}'

    try:
      comment_list = self.send_tapd_request_get(get_comments_api)
      return comment_list
    except Exception as e:
      logging.error(f'Failed to get comments from Tapd. Error: {e}')
      return []

  def get_stories_new(self):
    get_stories_api = '/api/tapd/external/common/getEntryBySource/story/'
    story_list = []
    request_body = {
      "workspace_id": self.workspace_id
    }

    try:
      story_list = self.send_tapd_request_post(get_stories_api, request_body=request_body)
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')

    return story_list

  def edit_story(self, edit_fields):
    edit_story_api = '/api/tapd/external/common/editEntry/story/'
    request_body = {
      "workspace_id": self.workspace_id,
      "id": edit_fields['story_id'],
      "custom_field_one": edit_fields['task_url']
    }
    try:
      response = self.send_tapd_request_post(edit_story_api, request_body=request_body)
      logging.info("Update Story is success", response)
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')

  def get_task(self):
    get_tasks_api = '/api/tapd/external/common/getEntryBySource/task/'
    request_body = {
      "workspace_id": self.workspace_id
    }

    try:
      task_list = self.send_tapd_request_post(get_tasks_api, request_body=request_body)
      return task_list
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')
      return []

  def get_images(self, image_path):
    get_image_api = f'api/tapd/external/image/{self.project}?workspaceId={self.workspace_id}&imagePath={image_path}'

    try:
      response = self.send_tapd_request_get(get_image_api)
      return response['data']['Attachment']['download_url']
    except Exception as e:
      logging.error(f'Failed to get comments from Tapd. Error: {e}')
      return {}

  def send_tapd_request_get(self, method):
    for i in range(self.max_retries):
      try:
        response = requests.get(self.api_url + method, timeout=30)
        response.raise_for_status()
        return response.json()

      except requests.exceptions.RequestException as e:
        if i < self.max_retries - 1:
          print("Retrying...")
          time.sleep(5)  # Wait for 5 seconds before retrying
        else:
          logging.error(f'Failed to send requests to TAPD. Error: {e}')
      except Exception as e:
        logging.error(f'Failed to send requests to TAPD. Error: {e}')

  def send_tapd_request_post(self, method, request_body):
    for i in range(self.max_retries):
      try:
        response = requests.post(self.api_url + method + self.project, json=request_body, timeout=60)
        response.raise_for_status()
        return response.json()

      except requests.exceptions.RequestException as e:
        if i < self.max_retries - 1:
          print("Retrying...")
          time.sleep(10)  # Wait for 5 seconds before retrying
        else:
          logging.error(f'Failed to send requests to TAPD. Error: {e}')
      except Exception as e:
        logging.error(f'Failed to send requests to TAPD. Error: {e}')
