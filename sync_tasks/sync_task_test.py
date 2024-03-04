import pytest

from phabricator import Phabricator
import sync_tasks
import configparser
import json
from tapd import Tapd

config = configparser.ConfigParser()
config.read(sync_tasks.get_env('test'))
phabricator = Phabricator(config)
tapd = Tapd(config)

username_to_phabricator_api_token_map = json.loads(config['phabricator']['api_token_map'])
default_api_token = config['phabricator']['api_token']

test_task_fields = {
  "id": "1159680598001066107",
  "workspaceId": 67664246,
  "name": "Testing sub_task creation",
  "description": "This is testing title",
  "url": "https://www.tapd.cn/67664246/prong/stories/view/1159680598001066107",
  "status": "Open",
  "priority": "EMPTY",
  "category": "Release Hub",
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
  "description": "<img src='/tfl/captures/2023-11/tapd_59680598_base64_1700471623_194.png' width='80%'/>",
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

create_sub_task_fields = {
  "custom_field_six": "",
  "custom_field_50": "",
  "has_attachment": "0",
  "workspace_id": "59680598",
  "custom_field_14": "",
  "custom_field_15": "",
  "custom_field_12": "",
  "custom_field_13": "",
  "custom_field_one": "",
  "custom_field_10": "",
  "custom_field_11": "",
  "exceed": "0",
  "custom_field_seven": "",
  "modified": "2023-11-17 17:24:05",
  "id": "1159680598001066124",
  "custom_field_18": "",
  "custom_field_19": "",
  "custom_field_16": "",
  "custom_field_17": "",
  "created": "2023-11-17 17:24:00",
  "remain": "0",
  "completed": None,
  "priority": "3",
  "custom_field_9": "",
  "iteration_id": "0",
  "custom_field_25": "",
  "custom_field_26": "",
  "custom_field_23": "",
  "custom_field_24": "",
  "custom_field_21": "",
  "custom_field_22": "",
  "custom_field_20": "",
  "name": "[web] refactor resource",
  "custom_field_29": "",
  "begin": "2023-11-06",
  "effort_completed": "0",
  "custom_field_27": "",
  "status": "progressing",
  "custom_field_28": "",
  "release_id": "0",
  "custom_field_four": "",
  "story_id": "1159680598001066107",
  "description": "",
  "effort": None,
  "custom_field_36": "",
  "custom_field_37": "",
  "custom_field_34": "",
  "custom_field_35": "",
  "custom_field_32": "",
  "custom_field_eight": "",
  "custom_field_33": "",
  "custom_field_30": "",
  "custom_field_31": "",
  "priority_label": "3",
  "custom_field_38": "",
  "custom_field_39": "",
  "owner": "christian.gabriel.isjwara;",
  "cc": "",
  "creator": "christian.gabriel.isjwara",
  "custom_field_40": "",
  "label": "",
  "custom_field_47": "",
  "custom_field_48": "",
  "custom_field_45": "",
  "custom_field_46": "",
  "custom_field_43": "",
  "custom_plan_field_3": "0",
  "due": "2023-11-30",
  "custom_field_44": "",
  "custom_plan_field_4": "0",
  "custom_field_41": "",
  "custom_plan_field_1": "0",
  "custom_field_three": "",
  "custom_field_42": "",
  "custom_plan_field_2": "0",
  "progress": "0",
  "custom_plan_field_5": "0",
  "custom_field_five": "",
  "custom_field_two": "",
  "custom_field_49": ""
}

task_response = {
  'object': {
    'id': 77870,
    'phid': 'PHID-TASK-v3mnb4ue7ew6yu344pvr'
  },
  'transactions': [
    {'phid': 'PHID-XACT-TASK-mhpbgzx7vkxmfhd'},
    {'phid': 'PHID-XACT-TASK-jf3xvapc5jpcyza'},
    {'phid': 'PHID-XACT-TASK-wwr2xvxb3dbp4ef'},
    {'phid': 'PHID-XACT-TASK-ts43vvkmhu5zs44'},
    {'phid': 'PHID-XACT-TASK-qe6tbgfm5offqeo'},
    {'phid': 'PHID-XACT-TASK-nko63uwp7v5mi4x'},
    {'phid': 'PHID-XACT-TASK-vy2iwrtxfdnortq'},
    {'phid': 'PHID-XACT-TASK-n425qnvzre6g6f6'},
    {'phid': 'PHID-XACT-TASK-l4ufva52hfkf7yx'}
  ]}


@pytest.mark.run(order=1)
def test_create_task():
  sync_fields = sync_tasks.format_create_task_fields(phabricator, test_task_fields, tapd)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(
    username_to_phabricator_api_token_map,
    test_task_fields["creator"],
    default_api_token
  )
  phabricator.create_update_task(sync_fields)


@pytest.mark.run(order=2)
def test_update_task():
  sync_fields = sync_tasks.format_create_task_fields(phabricator, update_task_fields, tapd)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(
    username_to_phabricator_api_token_map,
    update_task_fields["creator"],
    default_api_token
  )
  sync_fields['task_id'] = 77799
  phabricator.create_update_task(sync_fields)


@pytest.mark.run(order=3)
def test_create_comment():
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map, task_id_to_phabricator_task_map = sync_tasks.create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list)
  create_comment_fields = {
    'task_id': story_id_to_phabricator_task_map[test_task_fields['id']]['id'],
    'comment': "This is a comment made from Unit Testing",
    'commentator_api_token': default_api_token
  }
  phabricator.create_comment(create_comment_fields)


@pytest.mark.run(order=4)
def test_create_sub_task():
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map, task_id_to_phabricator_task_map = sync_tasks.create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list)
  phabricator_parent_task = story_id_to_phabricator_task_map.get(create_sub_task_fields["story_id"])
  create_sub_task_fields["phid"] = phabricator_parent_task["phid"]
  sync_fields = sync_tasks.format_create_sub_task_fields(phabricator, create_sub_task_fields)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(
    username_to_phabricator_api_token_map,
    test_task_fields["creator"],
    default_api_token
  )
  phabricator.create_update_subtask(sync_fields)


@pytest.mark.run(order=5)
def test_reference_phabricator_task():
  if task_response:
    update_story_fields = {
      'task_url': "https://code.yangqianguan.com/T" + str(task_response['object']['id']),
      'id': test_task_fields['id']
    }
    tapd.edit_story(update_story_fields)


def test_change_sub_task_category():
  tapd_task = {
    "custom_field_six": "",
    "custom_field_50": "",
    "has_attachment": "0",
    "workspace_id": "59680598",
    "custom_field_14": "",
    "custom_field_15": "",
    "custom_field_12": "",
    "custom_field_13": "",
    "custom_field_one": "",
    "custom_field_10": "",
    "custom_field_11": "",
    "exceed": "0",
    "custom_field_seven": "",
    "modified": "2023-11-17 17:24:05",
    "id": "1159680598001066124",
    "custom_field_18": "",
    "custom_field_19": "",
    "custom_field_16": "",
    "custom_field_17": "",
    "created": "2023-11-17 17:24:00",
    "remain": "0",
    "completed": None,
    "priority": "3",
    "custom_field_9": "",
    "iteration_id": "0",
    "custom_field_25": "",
    "custom_field_26": "",
    "custom_field_23": "",
    "custom_field_24": "",
    "custom_field_21": "",
    "custom_field_22": "",
    "custom_field_20": "",
    "name": "[web] refactor resource",
    "custom_field_29": "",
    "begin": "2023-11-06",
    "effort_completed": "0",
    "custom_field_27": "",
    "status": "progressing",
    "custom_field_28": "",
    "release_id": "0",
    "custom_field_four": "",
    "story_id": "1159680598001066107",
    "description": "",
    "effort": None,
    "custom_field_36": "",
    "custom_field_37": "",
    "custom_field_34": "",
    "custom_field_35": "",
    "custom_field_32": "",
    "custom_field_eight": "",
    "custom_field_33": "",
    "custom_field_30": "",
    "custom_field_31": "",
    "priority_label": "3",
    "custom_field_38": "",
    "custom_field_39": "",
    "owner": "christian.gabriel.isjwara;",
    "cc": "",
    "creator": "christian.gabriel.isjwara",
    "custom_field_40": "",
    "label": "",
    "custom_field_47": "",
    "custom_field_48": "",
    "custom_field_45": "",
    "custom_field_46": "",
    "custom_field_43": "",
    "custom_plan_field_3": "0",
    "due": "2023-11-30",
    "custom_field_44": "",
    "custom_plan_field_4": "0",
    "custom_field_41": "",
    "custom_plan_field_1": "0",
    "custom_field_three": "",
    "custom_field_42": "",
    "custom_plan_field_2": "0",
    "progress": "0",
    "custom_plan_field_5": "0",
    "custom_field_five": "",
    "custom_field_two": "",
    "custom_field_49": ""
  }

  phabricator_parent_task = {
    'id': "77870",
    'phid': 'PHID-TASK-v3mnb4ue7ew6yu344pvr',
    'title': "Testing sub_task creation",
    'description': "This is testing title\n\nTAPD Story Link: https://www.tapd.cn/59680598/prong/stories/view/1159680598001066569",
    'owner': "christian,.gabriel.isjwara",
    'priority': "high",
    'developers': "christian,.gabriel.isjwara",
    'testers': None,
    'column': "ReleaseHub",
    'status': "open"
  }

  phabricator_task_fields = {
    'id': "78071",
    'phid': 'PHID-TASK-v3mnb4ue7ew6yu344pvr',
    'title': "Testing sub_task creation",
    'description': "This is testing title\n\nTAPD Story Link: https://www.tapd.cn/59680598/prong/stories/view/1159680598001066569",
    'owner': "christian,.gabriel.isjwara",
    'priority': "high",
    'developers': "christian,.gabriel.isjwara",
    'testers': None,
    'column': None,
    'status': "open"
  }
  
  sync_fields = sync_tasks.format_create_sub_task_fields(phabricator, tapd_task, phabricator_parent_task)
  sync_fields = sync_tasks.format_update_sub_task_fields(sync_fields, phabricator_task_fields)
  sync_fields['creator_api_token'] = sync_tasks.get_creator_api_token(username_to_phabricator_api_token_map, tapd_task['creator'], default_api_token)
  phabricator.create_update_subtask(sync_fields)


def test_invalidate_task():
  task = {
    'phid': "PHID-TASK-v3mnb4ue7ew6yu344pvr"
  }
  sync_fields = sync_tasks.invalidate_task(task)
  sync_fields['creator_api_token'] = default_api_token
  phabricator.create_update_task(sync_fields)


def test_get_invalidated_tasks():
  phabricator_task_list = phabricator.get_tasks([], None)
  story_id_to_phabricator_task_map, task_id_to_phabricator_task_map = sync_tasks.create_tapd_story_and_tapd_task_to_phabricator_task_mapping(phabricator_task_list)
  invalidated_tasks = []
  invalidated_subtasks = []

  # Invalidate Unused Tasks:
  tapd_all_story_list = tapd.get_all_stories()
  tapd_story_id_set = set(sync_tasks.extract_tapd_story_id(tapd_all_story_list))
  phabricator_story_id_set = set(story_id_to_phabricator_task_map.keys())
  difference = phabricator_story_id_set - tapd_story_id_set

  for tapd_story_id in difference:
    phabricator_task = story_id_to_phabricator_task_map[tapd_story_id]
    invalidated_tasks.append(phabricator_task['id'])

  # Invalidate Unused Subtask
  tapd_task_list = tapd.get_all_task()

  tapd_task_id_list = sync_tasks.extract_tapd_task_id(tapd_task_list)
  tapd_task_id_set = set(tapd_task_id_list)
  phabricator_task_id_set = set(task_id_to_phabricator_task_map.keys())

  difference = phabricator_task_id_set - tapd_task_id_set

  for tapd_task_id in difference:
    phabricator_subtask = task_id_to_phabricator_task_map[tapd_task_id]
    invalidated_subtasks.append(phabricator_subtask['id'])

  print(invalidated_tasks)
  print(invalidated_subtasks)


test_create_default_user_fields = {
  "id": "1159680598001066107",
  "workspaceId": 67664246,
  "name": "Testing sub_task creation",
  "description": "This is testing title",
  "url": "https://www.tapd.cn/67664246/prong/stories/view/1159680598001066107",
  "status": "Open",
  "priority": "EMPTY",
  "category": "Release Hub",
  "creator": "advis.tasyah.mulia",
  "created": 1698031325000,
  "owner": "王禹丹;",
  "developer": "christian.gabriel.isjwara;",
  "qa": "james.surya.seputro;",
  "modified": 1698031367000,
  "begin": 1697990400000,
  "due": 1697990400000
}


def test_create_default_user():
  sync_fields = sync_tasks.format_create_task_fields(phabricator, test_create_default_user_fields, tapd)
  sync_fields["creator_api_token"] = sync_tasks.get_creator_api_token(
    username_to_phabricator_api_token_map,
    test_task_fields["creator"],
    default_api_token
  )
  response = phabricator.create_update_task(sync_fields)
  print(response)
