import os
import subprocess
import random
import time
import traceback
import configparser
import sys
import logging
from logging.handlers import RotatingFileHandler
import argparse
import re

sync_repos_path = os.path.dirname(__file__)
lib_path = os.path.join(sync_repos_path, 'lib')
sys.path.append(lib_path)
from easygoogletranslate import EasyGoogleTranslate
from git import Repo

config = configparser.ConfigParser()
https_proxy = None

EXCLUDED_FILES = ['.git', 'README.md']
INDO_BACKEND_EMAILS = [
  "christian.gabriel.isjwara@fintopia.tech",
  "dewy.yuliana@fintopia.tech",
  "himawan.saputra.utama@fintopia.tech",
  "i.gede.agung.krisna.pamungkas@fintopia.tech",
  "andrey.martin@fintopia.tech",
  "hafiz.siregar@fintopia.tech",
  "aflah.nadhif@fintopia.tech",
  "mario.claudius@fintopia.tech"
]

INDO_FRONTEND_EMAILS = [
  "ega.frandika@fintopia.tech",
  "dante.clericuzio@fintopia.tech",
  "kenneth.k.chang@fintopia.tech"
]

INDO_ANDROID_EMAILS = [
  "m.ridho.saputra@fintopia.tech"
]

INDO_IOS_EMAILS = [
  "barry.juans@fintopia.tech",
]

INDO_DEVOPS_EMAILS = [
  "danny.restu@fintopia.tech",
  "steven.agustinus@fintopia.tech"
]

INDO_ENGINEER_EMAIL_TO_JOIN_DATE_MAP = {
  "christian.gabriel.isjwara@fintopia.tech": "2023-02-23",
  "dewy.yuliana@fintopia.tech": "2022-10-03",
  "himawan.saputra.utama@fintopia.tech": "2022-11-07",
  "i.gede.agung.krisna.pamungkas@fintopia.tech": "2022-11-07",
  "andrey.martin@fintopia.tech": "2023-03-20",
  "hafiz.siregar@fintopia.tech": "2024-01-24",
  "aflah.nadhif@fintopia.tech": "2024-07-26",
  "mario.claudius@fintopia.tech": "2024-07-29",
  "ega.frandika@fintopia.tech": "2022-07-19",
  "dante.clericuzio@fintopia.tech": "2022-10-06",
  "kenneth.k.chang@fintopia.tech": "2023-06-12",
  "m.ridho.saputra@fintopia.tech": "2023-05-08",
  "barry.juans@fintopia.tech": "2023-04-27",
  "danny.restu@fintopia.tech": "2023-12-21",
  "steven.agustinus@fintopia.tech": "2024-06-10"
}


def compare_engineer_join_date_before_commit_date(engineer_email, commit_date):
  return INDO_ENGINEER_EMAIL_TO_JOIN_DATE_MAP.get(engineer_email) < commit_date


def replace_author(repo_type, author_email, commit_authored_date):
  if repo_type == 'backend' and author_email not in INDO_BACKEND_EMAILS:
    while True:
      engineer_email = INDO_BACKEND_EMAILS[random.randint(0, len(INDO_BACKEND_EMAILS) - 1)]
      if compare_engineer_join_date_before_commit_date(engineer_email, commit_authored_date):
        return engineer_email

  elif repo_type == 'frontend' and author_email not in INDO_FRONTEND_EMAILS:
    return INDO_FRONTEND_EMAILS[random.randint(0, len(INDO_FRONTEND_EMAILS) - 1)]

  elif repo_type == 'android' and author_email not in INDO_ANDROID_EMAILS:
    return INDO_ANDROID_EMAILS[random.randint(0, len(INDO_ANDROID_EMAILS) - 1)]

  elif repo_type == 'ios' and author_email not in INDO_IOS_EMAILS:
    return INDO_IOS_EMAILS[random.randint(0, len(INDO_IOS_EMAILS) - 1)]

  elif repo_type == 'devops' and author_email not in INDO_DEVOPS_EMAILS:
    while True:
      engineer_email = INDO_DEVOPS_EMAILS[random.randint(0, len(INDO_DEVOPS_EMAILS) - 1)]
      if compare_engineer_join_date_before_commit_date(engineer_email, commit_authored_date):
        return engineer_email
  else:
    return author_email


def git_commit(author_name, author_email, commit_message, commit_date, commit_authored_date, target_repo_path):
  try:
    # git add --all
    subprocess.check_output(['git', '-C', target_repo_path, 'add', '--all'])

    # git commit -m <message> --date=<date> --author=<author>
    command = ['git', '-C', target_repo_path, 'commit']
    command += ['-m', commit_message]
    command += ['--date', commit_authored_date]
    command += ['--author', "{} <{}>".format(author_name, author_email)]
    env = {"GIT_COMMITTER_DATE": commit_date}
    subprocess.check_call(command, env=env)
  except subprocess.CalledProcessError as e:
    print("Error while committing to the repository: ", e)
    tb = traceback.format_exc()
    print(tb)


def git_push(target_repo_path):
  try:
    # git push origin master
    subprocess.check_output(['git', '-C', target_repo_path, 'push', "origin", "master"])

    command = ['git', '-C', target_repo_path, 'log', '--oneline', '-1']
    last_git_log = subprocess.check_output(command).decode('utf-8').strip()
    print("Push target repo successful: ", last_git_log)
  except subprocess.CalledProcessError as e:
    print("Error while pushing to the repository: ", e)
    tb = traceback.format_exc()
    print(tb)


def checkout_commit_or_branch(repo_path, commit_or_branch):
  command = ['git', '-c', 'advice.detachedHead=false', 'checkout', commit_or_branch]
  try:
    subprocess.run(command, cwd=repo_path, check=True)
    print("Source repo checked out:", commit_or_branch)
  except subprocess.CalledProcessError as e:
    print("Error in checkout:", e)


def translate_text(text):
  translator = EasyGoogleTranslate(
    source_language='zh-CN',
    target_language='en',
    timeout=500,
    proxy=https_proxy)
  translated_text = translator.translate(text)
  return translated_text


def format_commit_message(commit_message):
  # Remove title prefixes, e.g. [ec][mex]
  title_pattern = r'^\s*\[.*\]\s*(.+\n)'
  commit_message = re.sub(title_pattern, r'\1', commit_message)

  # Add new line before summary
  summary_pattern = 'Summary'
  commit_message = re.sub(rf'{summary_pattern}.*', rf'\n{summary_pattern}', commit_message)

  # Change reviewers and remove diff reference
  keywords = ['Reviewers:', 'Reviewed By:', 'Subscribers:']
  for word in keywords:
    commit_message = re.sub(rf'{word}.*', rf'{word} #indo-dev', commit_message)

  commit_message = re.sub(rf'Differential Revision:.+\n', '', commit_message)

  # Remove TAPD link
  tapd_keyword = r'https://www.tapd.cn'
  commit_message = re.sub(rf'{tapd_keyword}[^\s\n]*([\n\s])', r'\1', commit_message)

  # Remove story user
  user_keyword = r'--user='
  commit_message = re.sub(rf'{user_keyword}[^\s\n]*([\n\s])', r'\1', commit_message)

  # Translate
  commit_message = translate_text(commit_message[:1000])

  # Pass git hook
  if 'Reviewed By' not in commit_message:
    commit_message += '\nReviewed By: #indo-dev\n'

  return commit_message


def continuous_extract_commits(repo_type, source_repo_path, target_repo_path):
  try:
    repo = Repo(source_repo_path)
    head_commit_before_pull = repo.head.commit

    pull_repo(source_repo_path)
    pull_repo(target_repo_path)
    head_commit_after_pull = repo.head.commit

    commit_range = "{}..{}".format(head_commit_before_pull.hexsha, head_commit_after_pull.hexsha)
    command = ["git", "rev-list", "--ancestry-path", commit_range]
    commit_hashes = subprocess.check_output(command, cwd=source_repo_path).splitlines()
    commits = get_commit_objects(repo, reversed(commit_hashes))

    extract_commits_and_push(repo_type, commits, source_repo_path, target_repo_path)

  except Exception as e:
    checkout_commit_or_branch(source_repo_path, "master")
    print("Error in continuous_extract_commits:", e)


def get_commit_objects(repo, commit_hashes):
  commit_objects = []
  for commit_hash in commit_hashes:
    commit = repo.commit(commit_hash.strip().decode("utf-8").strip())
    commit_objects.append(commit)
  return commit_objects


def extract_commits_and_push(repo_type, commits, source_repo_path, target_repo_path):
  try:
    for commit in commits:
      # Filter out other country commit
      other_country_keywords = config.get('DEFAULT', 'other_country_keywords')
      keywords = other_country_keywords.replace(' ', '').split(',')
      translated_text = str(translate_text(commit.message[:1000])).lower()

      if any(keyword in translated_text for keyword in keywords):
        print("Skip commit ", commit.hexsha, " for other country")
        continue

      # Checkout to commit
      checkout_commit_or_branch(source_repo_path, commit.hexsha)
      # Copy all files from ec to ec-experiment
      for item in os.listdir(source_repo_path):
        item_path = os.path.join(source_repo_path, item)
        if item not in EXCLUDED_FILES:
          subprocess.run(['cp', '-R', item_path, target_repo_path], check=True)

      # Git commit
      commit_message = format_commit_message(commit.message)

      command = ["git", "show", "--format=%ci", "--no-patch", commit.hexsha]
      commit_date = subprocess.check_output(command, cwd=source_repo_path, text=True).strip()

      command = ["git", "show", "-s", "--format=%ad", "--date=iso", commit.hexsha]
      commit_authored_date = subprocess.check_output(command, cwd=source_repo_path, text=True).strip()

      author_email = commit.author.email
      author_email = replace_author(repo_type, author_email, commit_authored_date)
      author_name = author_email[:author_email.index('@')]
      git_commit(author_name, author_email, commit_message, commit_date, commit_authored_date, target_repo_path)

      git_push(target_repo_path)

      # Checkout to master
      checkout_commit_or_branch(source_repo_path, "master")

  except Exception as e:
    checkout_commit_or_branch(source_repo_path, "master")
    tb = traceback.format_exc()
    print("Error in extract and push:", e)
    print(tb)


def does_repository_exist(repo_path):
  path_to_git = os.path.join(repo_path, '.git')
  return os.path.exists(path_to_git)


def clone_repository(repo_address, repo_path):
  try:
    # Clone Repository
    command = ["git", "clone", repo_address, repo_path]
    subprocess.run(command, check=True)
    repo_name = repo_address[repo_address.rindex('/') + 1: repo_address.index('.git')]
    print("Repository " + repo_name + " cloned successfully.")

    subprocess.check_output(['git', '-C', repo_path, 'config', 'user.name', 'prod_ali'])
    subprocess.check_output(['git', '-C', repo_path, 'config', 'user.email', 'prod_ali@fintopia.tech'])
  except subprocess.CalledProcessError as e:
    print("An error occurred:", e)


def set_initial_commit_to_head(repo_path, sync_commits_since):
  command = ["git", "log", "--reverse", "--since=" + sync_commits_since, "--format=%H"]
  git_log = subprocess.check_output(command, cwd=repo_path, encoding='utf-8').splitlines()

  if len(git_log) == 0:
    print('There is no commit after {}', sync_commits_since)
    return

  first_commit_hash = git_log[0]

  command = ["git", "reset", "--hard", first_commit_hash]
  subprocess.run(command, cwd=repo_path)


def pull_repo(repo):
  try:
    command = ['git', 'pull']
    subprocess.run(command, cwd=repo, check=True)
    print("Git pull successful.")
  except subprocess.CalledProcessError as e:
    print(f"Git pull failed with return code {e.returncode}.")


def run_push_commits(repo):
  print('Start syncing repo: ', repo)

  sync_repo = config.getboolean(repo, 'sync')
  if not sync_repo:
    print('Skipped repo: ', repo)
    return

  work_dir = config.get(repo, 'work_dir')
  source_repo_address = config.get(repo, 'source_repo_address')
  target_repo_address = config.get(repo, 'target_repo_address')
  source_repo_path = work_dir + repo + '_source_repo'
  target_repo_path = work_dir + repo + '_target_repo'
  sync_commits_since = config.get(repo, 'sync_commits_since')

  # Clone repos if not exist
  if not does_repository_exist(source_repo_path):
    clone_repository(source_repo_address, source_repo_path)
    set_initial_commit_to_head(source_repo_path, sync_commits_since)

  if not does_repository_exist(target_repo_path):
    clone_repository(target_repo_address, target_repo_path)

  repo_type = config.get(repo, 'type')
  continuous_extract_commits(repo_type, source_repo_path, target_repo_path)

  subprocess.run(['git', '-C', source_repo_path, 'gc', '--auto'])
  subprocess.run(['git', '-C', target_repo_path, 'gc', '--auto'])
  print('End syncing repo: ', repo)


def setup_logging(log_file):
  max_file_size = 200 * 1024 * 1024  # 200 MB

  handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=max_file_size,
    backupCount=2
  )

  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
  handler.setFormatter(formatter)

  logger = logging.getLogger()
  logger.addHandler(handler)
  logger.setLevel(logging.DEBUG)


def load_config(env):
  config.read(f'{sync_repos_path}/config.{env}.ini')
  return config


def get_env(env):
  if not env:
    env = 'test'
  return env


def set_proxy():
  global https_proxy
  try:
    https_proxy = config.get('DEFAULT', 'https_proxy')
    print('Using https_proxy ', https_proxy)
  except configparser.NoOptionError:
    print('Config [DEFAULT][https_proxy] is not found, using direct connection')


def get_time_sleep():
  try:
    delay = config.getfloat('DEFAULT', 'time_sleep')
    print('Time between each loop is ', delay)
    return delay
  except configparser.NoOptionError:
    print('Config [DEFAULT][sleep] is not found, using default instead')
    return 600


def main():
  parser = argparse.ArgumentParser(description='Sync Repo Script')
  parser.add_argument('--log-file', help='Path to the log file')
  parser.add_argument('--env', help='Environment')

  args = parser.parse_args()

  if args.log_file:
    setup_logging(args.log_file)

  env = get_env(args.env)

  # Infinite Loop
  while True:
    load_config(env)
    set_proxy()
    sleep = get_time_sleep()
    for repo in config.sections():
      run_push_commits(repo)
    time.sleep(sleep)


main()
