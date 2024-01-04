import logging
import requests
import base64
import time


class Phabricator:
  def __init__(self, config):
    section = 'phabricator'

    self.project_id = config.get(section, 'project_id')
    self.api_token = config.get(section, 'api_token')
    self.api_url = config.get(section, 'api_url')
    self.headers = config.get(section, 'headers')
    self.max_retries = config.getint(section, 'max_retries')
    self.sleep = config.getint(section, 'sleep')

  def create_update_task(self, sync_fields):
    create_update_task_api = 'maniphest.edit'

    request_data = {
      'api.token': sync_fields['creator_api_token'],
      'transactions[0][type]': 'projects.add',
      'transactions[0][value][0]': self.project_id
    }

    sync_fields.pop('creator_api_token')

    if 'task_id' in sync_fields:
      request_data['objectIdentifier'] = sync_fields['task_id']
      sync_fields.pop('task_id')

    transaction_count = 1
    developer_count = 0
    tester_count = 0
    for field, value in sync_fields.items():
      request_key = f'transactions[{transaction_count}]'

      if field in ['owner', 'developers', 'testers']:
        if field == 'owner':
          if value:
            request_data[request_key + '[type]'] = field
            request_data[request_key + '[value]'] = value
            transaction_count += 1

        if field == 'developers':
          for developer in value:
            if developer:
              request_data[request_key + f'[value][{developer_count}]'] = developer
              developer_count += 1

          if developer_count > 0:
            request_data[request_key + '[type]'] = 'custom.maniphest:' + field
            transaction_count += 1

        elif field == 'testers':
          for tester in value:
            if tester:
              request_data[request_key + f'[value][{tester_count}]'] = tester
              tester_count += 1

          if tester_count > 0:
            request_data[request_key + '[type]'] = 'custom.maniphest:' + field
            transaction_count += 1

      elif field == "column":
        column_id = self.get_column_id(value)
        if column_id:
          request_data[request_key + '[type]'] = field
          request_data[request_key + '[value][0]'] = column_id
          transaction_count += 1

      else:
        request_data[request_key + '[type]'] = field
        request_data[request_key + '[value]'] = value
        transaction_count += 1

    if transaction_count > 1:
      try:
        response = self.send_phabricator_request(create_update_task_api, request_data)
        logging.info(f'Update Task Successful, Changelist: {response}')
        return response["result"]
      except Exception as e:
        logging.error(f'Failed to update the task. Error: {e}')
        return None
    else:
      logging.error(f'Task not updated, No Changes.')

  def get_tasks(self, task_list, cursor):
    get_task_api = 'maniphest.search'
    request_data = {
      'api.token': self.api_token,
      'constraints[projects][0]': self.project_id,
      'constraints[statuses][0]': 'open',
      'attachments[columns]': True,
    }

    if cursor is not None:
      after = cursor.get('after')
      before = cursor.get('before')

      if after is not None:
        request_data['after'] = after

      if before is not None:
        request_data['before'] = before

    try:
      response = self.send_phabricator_request(get_task_api, request_data)
      task_result = response['result']
      task_list += task_result['data']

      if task_result.get('cursor'):
        cursor = task_result['cursor']
        if cursor.get('after'):
          task_list += self.get_tasks(task_list, task_result['cursor'])

      logging.info(f"Successfully get task from project")

      # return phabricator_task_list
      return task_list
    except Exception as e:
      logging.error(f'Failed to get phabricator tasks. Error: {e}')
      return []

  def get_user_id(self, username):
    get_user_api = 'user.search'
    request_data = {
      'api.token': self.api_token,
      'constraints[usernames][0]': username
    }

    try:
      response = self.send_phabricator_request(get_user_api, request_data)
      logging.info(f"Successfully get user id for user {response}")
      return response['result']['data'][0]['phid']

    except Exception as e:
      logging.error(f'Failed to fetch user. Error: {e}')
      return None

  def get_user_id_list(self, username_list):
    user_id_list = []
    for username in username_list:
      user_id = self.get_user_id(username)
      if user_id:
        user_id_list.append(user_id)
      else:
        logging.error(f'Failed to fetch user with username {username}')

    return user_id_list

  def get_column_id(self, column_name):
    get_column_api = "project.column.search"

    request_data = {
      'api.token': self.api_token,
      'constraints[projects][0]': self.project_id
    }

    try:
      response = self.send_phabricator_request(get_column_api, request_data)
      project_columns = response['result']['data']
      for column in project_columns:
        if column['fields']['name'] == column_name:
          logging.info(f"Successfully get column id of column {column_name}")
          return column['phid']

    except Exception as e:
      logging.error(f'Failed to fetch user. Error: {e}')
    return None

  def create_comment(self, comment_fields):
    update_task_api = 'maniphest.edit'
    request_data = {
      'api.token': comment_fields["commentator_api_token"],
      'objectIdentifier': comment_fields["task_id"],
      'transactions[0][type]': 'comment',
      'transactions[0][value]': comment_fields["comment"]
    }

    try:
      self.send_phabricator_request(update_task_api, request_data)
      logging.info(f'Successfully added comment to Task ID: {comment_fields["task_id"]}')

    except Exception as e:
      logging.error(f'Failed to make task comment for Task ID {comment_fields["task_id"]}, Error {e}')

  def create_update_subtask(self, sync_fields):
    create_update_task_api = 'maniphest.edit'

    request_data = {
      'api.token': sync_fields['creator_api_token'],
      'transactions[0][type]': 'projects.add',
      'transactions[0][value][0]': self.project_id
    }

    if 'task_id' in sync_fields:
      request_data['objectIdentifier'] = sync_fields['task_id']
      sync_fields.pop('task_id')

    sync_fields.pop('creator_api_token')
    transaction_count = 1
    for field, value in sync_fields.items():
      request_key = f'transactions[{transaction_count}]'

      if field == 'owner':
        if value:
          request_data[request_key + '[type]'] = field
          request_data[request_key + '[value]'] = value
          transaction_count += 1

      elif field == 'column':
        column_id = self.get_column_id(value)
        if column_id:
          request_data[request_key + '[type]'] = field
          request_data[request_key + '[value][0]'] = column_id
          transaction_count += 1

      else:
        request_data[request_key + '[type]'] = field
        request_data[request_key + '[value]'] = value
        transaction_count += 1
        
    if transaction_count > 1:
      try:
        response = self.send_phabricator_request(create_update_task_api, request_data)
        logging.info(f'Update Subtask Successful, Changelist: {response}')
      except Exception as e:
        logging.error(f'Failed to update the SubTask. Error: {e}')
    else:
      logging.error(f'SubTask not updated, No Changes.')

  def upload_file(self, file_path):
    upload_file_api = 'file.upload'
    file_encoding = base64.b64encode(requests.get(file_path, self.headers).content)

    request_data = {
      'api.token': self.api_token,
      'data_base64': file_encoding,
      'canCDN': True
    }
    try:
      response = self.send_phabricator_request(upload_file_api, request_data)
      logging.info(f'Successfully uploaded file. File Info: {response["result"]}')
      return response['result']
    except Exception as e:
      logging.error(f'Failed to upload file. Error: {e}')

  def get_file(self, phid):
    get_file_api = 'file.info'
    request_data = {
      'api.token': self.api_token,
      'phid': phid
    }

    try:
      response = self.send_phabricator_request(get_file_api, request_data)
      file_info = response['result']['objectName']
      logging.info(f'Successfully uploaded file. File Info: {file_info}')
      return file_info
    except Exception as e:
      logging.error(f'Failed to upload file. Error: {e}')
      return None

  def send_phabricator_request(self, method, request_data):
    for i in range(self.max_retries):
      try:
        phabricator_api_url = self.api_url + method

        response = requests.post(phabricator_api_url, request_data, timeout=60)

        response.raise_for_status()
        phabricator_response = response.json()
        if phabricator_response['error_code'] is None and phabricator_response['error_info'] is None:
          time.sleep(self.sleep)
          return phabricator_response

        raise Exception(phabricator_response["error_info"])
      except requests.exceptions.RequestException as e:
        if i < self.max_retries - 1:
          logging.info(f"Retrying {method} for the {i + 1} time...")
          time.sleep(self.sleep)  # Wait before retrying
        else:
          logging.error(f'Failed to create request to phabricator API. Request Error: {e}')
      except Exception as e:
        logging.error(f'Failed to create request to phabricator API. Error: {e}')
