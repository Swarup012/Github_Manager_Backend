import os
import requests
from dotenv import load_dotenv
import base64





def get_headers(token):
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

def create_issue(repo, title, body="", token=""):
    url = f"https://api.github.com/repos/{repo}/issues"
    data = {"title": title, "body": body}
    headers = get_headers(token)
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def list_issues(repo, token=""):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = get_headers(token)
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}

# ...existing code...

def delete_issue(repo, issue_number, token=""):
    
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    headers = get_headers(token)
    data = {"state": "closed"}
    response = requests.patch(url, headers=headers, json=data)
    return response.json() if response.status_code in [200, 201] else {"error": response.text}

# ...existing code...

# ...existing code...

def delete_all_issues(repo, token=""):
    """
    Closes all open issues in the specified repository.
    Returns a list of results for each issue.
    """
    issues = list_issues(repo, token)
    if not isinstance(issues, list):
        return {"error": issues.get("error", "Failed to fetch issues")}
    
    results = []
    for issue in issues:
        issue_number = issue.get("number")
        if issue_number:
            res = delete_issue(repo, issue_number, token)
            results.append({"issue_number": issue_number, "result": res})
    return results

def get_repo_info(repo, token=None):
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo}"
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        data = res.json()
        return {
            "name": data.get("name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "language": data.get("language"),
            "url": data.get("html_url"),
        }
    else:
        return {"error": res.text}

def update_readme(repo, new_content, commit_message, token):
    url = f"https://api.github.com/repos/{repo}/contents/README.md"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }



    # 1. Get current README (to fetch the SHA)
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code != 200:
        return {"error": "Failed to fetch README.md", "message": get_resp.text}

    sha = get_resp.json().get("sha")

    # 2. Encode content in Base64
    encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    # 3. Prepare request payload
    payload = {
        "message": commit_message,
        "content": encoded_content,
        "sha": sha,
    }

    # 4. PUT request to update the file
    put_resp = requests.put(url, headers=headers, json=payload)
    return put_resp.json()
