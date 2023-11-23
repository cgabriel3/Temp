import logging
import requests


class Tapd:
  def __init__(self, config):
    section = "tapd"
    self.config = config
    self.api_url = config.get(section, 'api_url')
    self.project = config.get(section, 'project')
    self.workspace_id = config.get(section, 'workspace_id')

  def get_stories(self):
    get_stories_api = f'api/tapd/external/story/getStoryBySource?source={self.project}'
    story_list = []

    try:
      story_list = self.send_tapd_request_get(get_stories_api)
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')

    return story_list

  def get_comments(self):
    get_comments_api = f'api/tapd/external/comment/getCommentBySource?source={self.project}'
    comment_list = []

    try:
      comment_list = self.send_tapd_request_get(get_comments_api)
    except Exception as e:
      logging.error(f'Failed to get comments from Tapd. Error: {e}')

    return comment_list

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

  def get_task(self):
    get_tasks_api = '/api/tapd/external/common/getEntryBySource/task/'
    task_list = []
    request_body = {
      "workspace_id": self.workspace_id
    }

    try:
      task_list = self.send_tapd_request_post(get_tasks_api, request_body=request_body)
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')

    return task_list

  def get_images(self, image_path):
    get_image_api = f'api/tapd/external/image/{self.project}?workspaceId={self.workspace_id}&imagePath={image_path}'
    image = {}

    try:
      response = self.send_tapd_request_get(get_image_api)
      image = response['data']['Attachment']['download_url']
    except Exception as e:
      logging.error(f'Failed to get comments from Tapd. Error: {e}')

    return image

  def send_tapd_request_get(self, method):
    try:
      response = requests.get(self.api_url + method, timeout=30)
      response.raise_for_status()
      return response.json()

    except requests.exceptions.RequestException as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')
    except Exception as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')

  def send_tapd_request_post(self, method, request_body):
    try:
      response = requests.post(self.api_url + method + self.project, json=request_body, timeout=30)
      response.raise_for_status()
      return response.json()

    except requests.exceptions.RequestException as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')
    except Exception as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')
