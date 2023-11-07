import logging
import requests


class Tapd:
  def __init__(self, config):
    section = "tapd"
    self.config = config
    self.api_url = config.get(section, 'api_url')
    self.project = config.get(section, 'project')

  def get_stories(self):
    get_stories_api = 'api/tapd/external/story/getStoryBySource?source='
    story_list = []

    try:
      story_list = self.send_tapd_request(get_stories_api)
    except Exception as e:
      logging.error(f'Failed to get stories from Tapd. Error: {e}')

    return story_list

  def get_comments(self):
    get_comments_api = 'api/tapd/external/comment/getCommentBySource?source='
    comment_list = []

    try:
      comment_list = self.send_tapd_request(get_comments_api)
    except Exception as e:
      logging.error(f'Failed to get comments from Tapd. Error: {e}')

    return comment_list

  def send_tapd_request(self, method):
    try:
      response = requests.get(self.api_url + method + self.project)
      response.raise_for_status()
      return response.json()

    except requests.exceptions.RequestException as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')
    except Exception as e:
      logging.error(f'Failed to send requests to TAPD. Error: {e}')
