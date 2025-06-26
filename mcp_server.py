from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github_client import create_issue, list_issues, update_readme,delete_issue, delete_all_issues, get_repo_info
from chatbot import ask_bot
import json

app = FastAPI()

# Allow CORS (Frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/mcp")
async def mcp_handler(req: Request):
    data = await req.json()
    user_input = data.get("input", "")
    repo = data.get("repo", "")
    github_token = data.get("github_token", "")
    gemini_key = data.get("gemini_key", "")

    if not user_input:
        return {"response": "❌ Please enter a command or question."}

    # Ask Gemini
    bot_response = ask_bot(user_input, gemini_key=gemini_key)
    print("🔹 Gemini raw:", bot_response)

    # Parse Gemini response
    try:
        clean = bot_response.strip("` \n")
        if clean.startswith("json"):
            clean = clean[4:].strip()
        parsed = json.loads(clean)
        action = parsed.get("action")
        payload = parsed.get("data", {})
    except Exception:
        return {"response": f"🤖 Gemini says: {bot_response}"}

    # === CREATE ISSUE ===
    if action == "create_issue":
        if not repo:
            return {"response": "❌ Please provide a GitHub repository name."}
        title = payload.get("title", "")
        body = payload.get("body", "")
        res = create_issue(repo, title, body, token=github_token)

        if "url" in res:
            return {
                "response": f"✅ Successfully created a GitHub issue titled **'{title}'**.\n\n🔗 [View Issue]({res['html_url']})"
            }
        else:
            return {"response": f"❌ Failed to create issue: {res.get('message', 'Unknown error')}"}

    # === UPDATE README ===
    elif action == "update_readme":
        if not repo:
            return {"response": "❌ Please provide a GitHub repository name."}
        content = payload.get("content", "")
        message = payload.get("message", "Update README via Gemini")

        res = update_readme(repo, content, message, token=github_token)

        if "commit" in res:
            commit_msg = res["commit"].get("message", "README updated.")
            return {
                "response": f"✅ Successfully updated the README with commit: **{commit_msg}**."
            }
        else:
            return {
                "response": f"❌ Failed to update README: {res.get('message', 'Unknown error')}"
            }

    # === LIST ISSUES ===
    elif action == "list_issues":
        if not repo:
            return {"response": "❌ Please provide a GitHub repository name."}
        issues = list_issues(repo, token=github_token)
        if isinstance(issues, list) and issues:
            titles = [f"• {i['title']}" for i in issues]
            return {"response": "📋 Open Issues:\n" + "\n".join(titles)}
        elif isinstance(issues, list) and not issues:
            return {"response": "✅ No open issues found in the repository."}
        else:
            return {
                "response": f"❌ GitHub Error: {issues.get('error', 'Unknown error')}"
            }
        
    # === DELETE ISSUE ===
    elif action == "delete_issue":
        if not repo:
            return {"response": "❌ Please provide a GitHub repository name."}
        issue_number = payload.get("issue_number")
        if not issue_number:
            return {"response": "❌ Please provide an issue number to delete."}
        res = delete_issue(repo, issue_number, token=github_token)
        if "state" in res and res["state"] == "closed":
            return {"response": f"✅ Issue #{issue_number} has been closed (deleted)."}
        else:
            return {"response": f"❌ Failed to delete issue: {res.get('error', res.get('message', 'Unknown error'))}"}
        
    # === DELETE ALL ISSUES ===
    elif action == "delete_all_issues":
        if not repo:
            return {"response": "❌ Please provide a GitHub repository name."}
        res = delete_all_issues(repo, token=github_token)
        if isinstance(res, list) and res:
            closed = [str(r["issue_number"]) for r in res if r["result"].get("state") == "closed"]
            failed = [str(r["issue_number"]) for r in res if r["result"].get("state") != "closed"]
            msg = ""
            if closed:
                msg += f"✅ Closed issues: {', '.join(closed)}.\n"
            if failed:
                msg += f"❌ Failed to close: {', '.join(failed)}."
            return {"response": msg or "No issues found to delete."}
        elif isinstance(res, list) and not res:
            return {"response": "✅ No open issues found to delete."}
        else:
            return {"response": f"❌ Error: {res.get('error', 'Unknown error')}"}
        
    elif action == "explain_repo":
     if not repo:
        return {"response": "❌ Repo name is required to explain."}
     info = get_repo_info(repo, token=github_token)
     if "error" in info:
         return {"response": f"❌ GitHub Error: {info['error']}"}
     description = info.get("description") or "No description available."
     stars = info.get("stars", 0)
     language = info.get("language", "Unknown")
     url = info.get("url", "")
     return {
         "response": f"📘 Repo: [{repo}]({url})\n"
                    f"🔤 Description: {description}\n"
                    f"⭐ Stars: {stars}\n"
                    f"💻 Language: {language}"
     }
        
    elif action == "get_issue_by_title":
        if not repo:
            return {"response": "❌ Repo name is required to fetch the issue."}
        title_query = payload.get("title", "").lower()
        issues = list_issues(repo, token=github_token)

        if isinstance(issues, list):
            for issue in issues:
                if issue["title"].lower() == title_query:
                    return {
                        "response": f"📌 Issue Found:\n\n**Title:** {issue['title']}\n\n**Body:** {issue.get('body', '(no description)')}\n\n🔗 {issue['html_url']}"
                    }
            return {"response": f"⚠️ No issue found with the title '{title_query}'."}
        else:
            return {"response": f"❌ GitHub Error: {issues.get('error', 'Unknown error')}"}
        
    elif action == "none":
     return {
        "response": "🤖 Sorry, I didn't understand that command. Try asking something like:\n"
                    "- Create an issue titled 'Fix bug'\n"
                    "- Show issues\n"
                    "- What is this repo for?\n"
                    "- Update README with description"
    }



    # === DEFAULT ===
    else:
        return {"response": f"🤖 Gemini says:\n\n{bot_response}"}
