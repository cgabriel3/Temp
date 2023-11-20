import pytest

from phabricator import Phabricator
import sync_tasks
import configparser
import json

config = configparser.ConfigParser()
config.read(sync_tasks.get_env('test'))
phabricator = Phabricator(config)

username_to_phabricator_api_token_map = json.loads(config['phabricator']['api_token_map'])
default_api_token = config['phabricator']['api_token']

test_task_fields = {
  "id": "9999999",
  "workspaceId": 67664246,
  "name": "This is made from Unit Testing",
  "description": "This is testing title",
  "url": "https://www.tapd.cn/67664246/prong/stories/view/9999999",
  "status": "Suspended",
  "priority": "EMPTY",
  "category": "Pre Assess",
  "creator": "advis.tasyah.mulia",
  "created": 1698031325000,
  "owner": "christian.gabriel.isjwara;",
  "developer": "christian.gabriel.isjwara;",
  "qa": "james.surya.seputro;",
  "modified": 1698031367000,
  "begin": 1697990400000,
  "due": 1697990400000
}

update_task_fields = {
  "id": "9999999",
  "workspaceId": 67664246,
  "name": "This is updated from Unit Testing",
  "description": "Updated Testing Description",
  "url": "https://www.tapd.cn/67664246/prong/stories/view/9999999",
  "status": "Assess Finished",
  "priority": "Nice To Have",
  "category": "Release Hub",
  "creator": "andrey.martin",
  "created": 1698031325000,
  "owner": "christian.gabriel.isjwara;",
  "developer": "andrey.martin;himawan.saputra.utama;",
  "qa": "james.surya.seputro;yulia.dewi;",
  "modified": 1698031367000,
  "begin": 1697990400000,
  "due": 1697990400000
}


@pytest.mark.run(order=1)
def test_create_task():
  sync_fields = sync_tasks.format_create_task_fields(phabricator, test_task_fields)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(username_to_phabricator_api_token_map, test_task_fields["creator"], default_api_token)
  phabricator.create_update_task(sync_fields)


@pytest.mark.run(order=2)
def test_update_task():
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map = sync_tasks.create_tapd_story_to_phabricator_task_mapping(phabricator_task_list)
  sync_fields = sync_tasks.format_create_task_fields(phabricator, update_task_fields)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(username_to_phabricator_api_token_map, update_task_fields["creator"], default_api_token)
  phabricator.create_update_task(sync_tasks.format_update_task_fields(sync_fields, story_id_to_phabricator_task_map[test_task_fields['id']]))


@pytest.mark.run(order=3)
def test_create_comment():
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map = sync_tasks.create_tapd_story_to_phabricator_task_mapping(phabricator_task_list)
  create_comment_fields = {
    'task_id': story_id_to_phabricator_task_map[test_task_fields['id']]['id'],
    'comment': "This is a comment made from Unit Testing",
    'commentator_api_token': default_api_token
  }
  phabricator.create_comment(create_comment_fields)
