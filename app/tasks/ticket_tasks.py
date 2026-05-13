def notify_project_members(emails: list[str], ticket_summary: str):
    for email in emails:
        print(
            f"[NOTIFICATION] "
            f"Sent to {email}: "
            f"New ticket created: {ticket_summary}"
        )