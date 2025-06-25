# GRC_Task_Reminder
Python script that demonstrates how to automate sending reminders for overdue tasks.

This example integrates with:

A project management tool (Jira/Asana via their APIs)
Slack/Teams for notifications
Uses a spreadsheet as a fallback data source

How to Use This Code:
Configuration:
Update the CONFIG dictionary with your actual API keys, webhook URLs, and file paths
Set the default_assignee to John's identifier in each system

Data Sources:
The script can pull from Jira, Asana, or a spreadsheet (default)
Change the source parameter when initializing TaskManager

Notification Channels:

Currently supports Slack and Microsoft Teams
Uncomment the one you want to use

Requirements:

Install required packages: pip install requests pandas openpyxl

Scheduling:

To run this daily, set it up as a cron job (Linux/Mac) or Task Scheduler (Windows)
Alternatively, deploy as a serverless function (AWS Lambda, Azure Functions, etc.)

This script provides a complete solution for the described automation scenario, with flexibility to work with different project management tools and notification channels.
