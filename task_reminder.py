import datetime
import requests
import pandas as pd
from typing import List, Dict

# Configuration - replace with your actual credentials and endpoints
CONFIG = {
    "jira": {
        "api_url": "https://your-domain.atlassian.net/rest/api/3",
        "email": "your-email@example.com",
        "api_token": "your-api-token"
    },
    "asana": {
        "api_url": "https://app.asana.com/api/1.0",
        "api_token": "your-asana-token"
    },
    "slack": {
        "webhook_url": "https://hooks.slack.com/services/your/webhook/url"
    },
    "teams": {
        "webhook_url": "https://outlook.office.com/webhook/your/webhook/url"
    },
    "spreadsheet_path": "tasks.xlsx",  # Fallback spreadsheet
    "default_assignee": "john@example.com",  # John's email/Slack handle
    "overdue_days_threshold": 3
}

class TaskManager:
    def __init__(self, source: str = "spreadsheet"):
        self.source = source
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Fetch overdue tasks from the selected source"""
        overdue_tasks = []
        today = datetime.date.today()
        
        if self.source == "jira":
            # Jira API implementation
            headers = {
                "Accept": "application/json",
                "Authorization": f"Basic {CONFIG['jira']['api_token']}"
            }
            query = {
                "jql": f"assignee = '{CONFIG['default_assignee']}' AND status != Done AND due < -{CONFIG['overdue_days_threshold']}d",
                "fields": "summary,duedate"
            }
            try:
                response = requests.get(
                    f"{CONFIG['jira']['api_url']}/search",
                    headers=headers,
                    params=query
                )
                response.raise_for_status()
                issues = response.json().get("issues", [])
                
                for issue in issues:
                    overdue_tasks.append({
                        "title": issue["fields"]["summary"],
                        "due_date": issue["fields"]["duedate"],
                        "assignee": CONFIG['default_assignee']
                    })
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from Jira: {e}")
        
        elif self.source == "asana":
            # Asana API implementation
            headers = {
                "Authorization": f"Bearer {CONFIG['asana']['api_token']}"
            }
            try:
                response = requests.get(
                    f"{CONFIG['asana']['api_url']}/tasks",
                    headers=headers,
                    params={
                        "assignee": CONFIG['default_assignee'],
                        "completed_since": "now",
                        "opt_fields": "name,due_on"
                    }
                )
                response.raise_for_status()
                tasks = response.json().get("data", [])
                
                for task in tasks:
                    if task.get("due_on"):
                        due_date = datetime.datetime.strptime(task["due_on"], "%Y-%m-%d").date()
                        if (today - due_date).days >= CONFIG['overdue_days_threshold']:
                            overdue_tasks.append({
                                "title": task["name"],
                                "due_date": task["due_on"],
                                "assignee": CONFIG['default_assignee']
                            })
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from Asana: {e}")
        
        else:
            # Fallback to spreadsheet
            try:
                df = pd.read_excel(CONFIG['spreadsheet_path'])
                for _, row in df.iterrows():
                    if (row['Assignee'] == CONFIG['default_assignee'] and 
                        pd.notna(row['Due Date']) and 
                        row['Status'] != 'Completed'):
                        due_date = row['Due Date'].date()
                        if (today - due_date).days >= CONFIG['overdue_days_threshold']:
                            overdue_tasks.append({
                                "title": row['Task Name'],
                                "due_date": str(due_date),
                                "assignee": row['Assignee']
                            })
            except Exception as e:
                print(f"Error reading spreadsheet: {e}")
        
        return overdue_tasks

class Notifier:
    @staticmethod
    def send_slack_notification(task: Dict):
        """Send notification to Slack"""
        message = {
            "text": f"🚨 Task Reminder for {task['assignee']}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Overdue Task Reminder*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Task:*\n{task['title']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Due Date:*\n{task['due_date']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Days Overdue:*\n{(datetime.date.today() - (task['due_date'] if isinstance(task['due_date'], datetime.date) else datetime.datetime.strptime(task['due_date'], '%Y-%m-%d').date())).days}"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                CONFIG['slack']['webhook_url'],
                json=message
            )
            response.raise_for_status()
            print(f"Slack notification sent for task: {task['title']}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Slack: {e}")

    @staticmethod
    def send_teams_notification(task: Dict):
        """Send notification to Microsoft Teams"""
        message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "Overdue Task Reminder",
            "sections": [{
                "activityTitle": f"🚨 Task Reminder for {task['assignee']}",
                "facts": [
                    {
                        "name": "Task",
                        "value": task['title']
                    },
                    {
                        "name": "Due Date",
                        "value": task['due_date']
                    },
                    {
                        "name": "Days Overdue",
                        "value": str((datetime.date.today() - (task['due_date'] if isinstance(task['due_date'], datetime.date) else datetime.datetime.strptime(task['due_date'], '%Y-%m-%d').date())).days)
                    }
                ],
                "markdown": True
            }]
        }
        
        try:
            response = requests.post(
                CONFIG['teams']['webhook_url'],
                json=message
            )
            response.raise_for_status()
            print(f"Teams notification sent for task: {task['title']}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Teams: {e}")

def main():
    # Initialize task manager (change source to "jira" or "asana" as needed)
    task_manager = TaskManager(source="spreadsheet")
    
    # Get overdue tasks
    overdue_tasks = task_manager.get_overdue_tasks()
    
    if not overdue_tasks:
        print("No overdue tasks found.")
        return
    
    # Send notifications for each overdue task
    for task in overdue_tasks:
        print(f"Sending reminder for overdue task: {task['title']}")
        
        # Send to Slack
        Notifier.send_slack_notification(task)
        
        # Alternatively, send to Teams
        # Notifier.send_teams_notification(task)

if __name__ == "__main__":
    main()