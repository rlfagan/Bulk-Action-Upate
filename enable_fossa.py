import os
import subprocess
import requests
import yaml
from time import sleep

# GitHub personal access token
token = 'ghp_xxxxxxxxxxxxxxx'
headers = {'Authorization': f'token {token}'}

# User or organization name
username_or_org = 'OrgName'

# Workflow content to add
workflow_content = {
    'on': {
        'push': {
            'branches': ['**']
        },
        'workflow_dispatch': None
    },
    'name': 'GH Action Bulk On-boarder',
    'jobs': {
        'fossa-scan': {
            'runs-on': 'ubuntu-latest',
            'steps': [
                {'uses': 'actions/checkout@v3'},
                {
                    'uses': 'fossas/fossa-action@main',
                    'with': {'api-key': '${{secrets.fossaApiKey}}'}
                }
            ]
        }
    }
}

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

# Function to update workflow file
def update_workflow_file(repo_dir):
    workflow_dir = os.path.join(repo_dir, '.github', 'workflows')
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_file = os.path.join(workflow_dir, 'link_checker.yml')
    
    with open(workflow_file, 'w') as f:
        yaml.safe_dump(workflow_content, f)
    
# Function to clone repository, update workflow, commit and push changes
def update_repository(repo):
    repo_name = repo.split("/")[1]
    repo_url = f'https://{token}@github.com/{repo}.git'
    local_repo_dir = f'/tmp/{repo_name}'
    
    try:
        # Clone the repository
        subprocess.run(['git', 'clone', repo_url, local_repo_dir], check=True)
        
        # Update the workflow file
        update_workflow_file(local_repo_dir)
        
        # Commit the changes
        subprocess.run(['git', '-C', local_repo_dir, 'add', '.'], check=True)
        subprocess.run(['git', '-C', local_repo_dir, 'commit', '-m', 'Update GitHub Actions workflow for Fossa scan'], check=True)
        
        # Push the changes
        subprocess.run(['git', '-C', local_repo_dir, 'push'], check=True)
        
        print(f'Successfully updated workflow for {repo}')
    except subprocess.CalledProcessError as e:
        print(f'Failed to update workflow for {repo}: {e}')
    finally:
        # Clean up the local repository directory
        subprocess.run(['rm', '-rf', local_repo_dir])

# Fetch repositories
repositories = fetch_repositories(username_or_org)

# Update each repository
for repo in repositories:
    update_repository(repo['full_name'])
    sleep(1)  # To avoid hitting rate limits
