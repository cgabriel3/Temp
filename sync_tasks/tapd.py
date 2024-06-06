import json
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
    self.sleep = config.getint(section, 'sleep')
    self.base_story_url = config.get(section, 'base_story_url')
    self.doc_template_id = config.get(section, 'doc_template_id')
    self.category_id_name_map = config.get(section, 'category_id_to_name_map')
    self.base_image_url = config.get(section, 'base_image_url')

  def get_updated_stories(self):
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

  def get_all_task(self):
    get_tasks_api = '/api/tapd/external/common/getEntryBySource/task/'
    all_task_list = []
    page = 1
    request_body = {
      "workspace_id": self.workspace_id,
      "limit": 50,
      "page": page
    }

    while True:
      try:
        task_list = self.send_tapd_request_post(get_tasks_api, request_body=request_body)
        all_task_list += task_list

        if len(task_list) < 50:
          break

        page += 1
        request_body["page"] = page
      except Exception as e:
        logging.error(f'Failed to get task from Tapd. Error: {e}')
        return []

    return all_task_list

  def get_images(self, image_path):
    try:
      if not self.check_if_image_tapd_url(image_path):
        raise ValueError(f'Not a TAPD Image URL {image_path}')
      image_path = image_path.replace("https://file.tapd.cn/", "")
      get_image_api = f'api/tapd/external/image/{self.project}?workspaceId={self.workspace_id}&imagePath={image_path}'
      response = self.send_tapd_request_get(get_image_api)
      return response['data']['Attachment']['download_url']
    except Exception as e:
      logging.error(f'Failed to get image from Tapd with URL {image_path}. Error: {e}')
      return {}

  def get_all_stories(self, modified_time):
    get_all_stories_api = f'/api/tapd/external/common/getEntryBySource/story/'
    page = 1
    all_story_list = []
    request_body = {
      "workspace_id": self.workspace_id,
      "limit": 50,
      "page": page,
      "modified": modified_time
    }

    while True:
      try:
        story_list = self.send_tapd_request_post(get_all_stories_api, request_body=request_body)
        all_story_list += story_list
        if len(story_list) < 50:
          break
        page += 1
        request_body["page"] = page
      except Exception as e:
        logging.error(f'Failed to get stories from Tapd. Error: {e}')
        return []

    return all_story_list

  def send_tapd_request_get(self, method):
    for i in range(self.max_retries):
      try:
        response = requests.get(self.api_url + method, timeout=30)
        response.raise_for_status()
        time.sleep(self.sleep)
        return response.json()

      except requests.exceptions.RequestException as e:
        if i < self.max_retries - 1:
          logging.info(f"Retrying {method} for the {i} time...")
          time.sleep(self.sleep)  # Wait before retrying
        else:
          logging.error(f'Failed to send requests to TAPD. Error: {e}')
      except Exception as e:
        logging.error(f'Failed to send requests to TAPD. Error: {e}')

  def send_tapd_request_post(self, method, request_body):
    for i in range(self.max_retries):
      try:
        response = requests.post(self.api_url + method + self.project, json=request_body, timeout=60)
        response.raise_for_status()
        time.sleep(self.sleep)
        return response.json()

      except requests.exceptions.RequestException as e:
        if i < self.max_retries - 1:
          logging.info(f"Retrying {method} for the {i + 1} time...")
          time.sleep(self.sleep)  # Wait before retrying
        else:
          logging.error(f'Failed to send requests to TAPD. Error: {e}')
      except Exception as e:
        logging.error(f'Failed to send requests to TAPD. Error: {e}')

  def generate_story_url(self, story_id):
    workspace_id_key = "workspace_id"
    story_url = self.base_story_url
    story_url = story_url.replace(workspace_id_key, self.workspace_id)
    return story_url + story_id

  def is_not_doc_template(self, template_id):
    return self.doc_template_id == template_id

  def get_category_name_from_category_id(self, category_id):
    category_name_to_id_map = json.loads(self.category_id_name_map)
    return category_name_to_id_map.get(category_id)

  def check_if_image_tapd_url(self, image_url):
    return image_url.startswith(self.base_image_url)
