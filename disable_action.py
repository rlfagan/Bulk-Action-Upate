import os
import subprocess
import requests
from time import sleep

# GitHub personal access token
token = 'your_github_token'
headers = {'Authorization': f'token {token}'}

# User or organization name
username_or_org = 'your_username_or_org'

# Function to fetch repositories
def fetch_repositories(username_or_org):
    repos = []
    page = 1
    while True:
        url = f'https://api.github.com/users/{username_or_org}/repos?page={page}&per_page=100'
        response = requests.get(url, headers=headers)
        
        if response.status_code == 403:  # Rate limit exceeded
            reset_time = int(response.headers['X-RateLimit-Reset'])
            sleep_time = reset_time - int(time.time()) + 1
            print(f'Rate limit exceeded. Sleeping for {sleep_time} seconds.')
            time.sleep(sleep_time)
            continue
        
        if response.status_code != 200:
            print(f'Failed to fetch repositories: {response.status_code}')
            break
        
        data = response.json()
        if not data:
            break
        
        repos.extend(data)
        page += 1
        
    return repos

# Function to disable workflow files
def disable_workflow_files(repo_dir):
    workflow_dir = os.path.join(repo_dir, '.github', 'workflows')
    if os.path.exists(workflow_dir):
        for filename in os.listdir(workflow_dir):
            file_path = os.path.join(workflow_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'w') as f:
                    f.write('# Workflow disabled\n')
                    print(f'Disabled workflow: {file_path}')

# Function to clone repository, disable workflows, commit and push changes
def update_repository(repo):
    repo_name = repo.split("/")[1]
    repo_url = f'https://{token}@github.com/{repo}.git'
    local_repo_dir = f'/tmp/{repo_name}'
    
    try:
        # Clone the repository
        subprocess.run(['git', 'clone', repo_url, local_repo_dir], check=True)
        
        # Disable the workflow files
        disable_workflow_files(local_repo_dir)
        
        # Commit the changes
        subprocess.run(['git', '-C', local_repo_dir, 'add', '.'], check=True)
        subprocess.run(['git', '-C', local_repo_dir, 'commit', '-m', 'Disable GitHub Actions workflows'], check=True)
        
        # Push the changes
        subprocess.run(['git', '-C', local_repo_dir, 'push'], check=True)
        
        print(f'Successfully disabled workflows for {repo}')
    except subprocess.CalledProcessError as e:
        print(f'Failed to disable workflows for {repo}: {e}')
    finally:
        # Clean up the local repository directory
        subprocess.run(['rm', '-rf', local_repo_dir])

# Fetch repositories
repositories = fetch_repositories(username_or_org)

# Update each repository
for repo in repositories:
    update_repository(repo['full_name'])
    sleep(1)  # To avoid hitting rate limits
