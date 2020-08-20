from snapbot.database import DatabaseWrapper, get_workspaces
from snapbot.slack import post_message


def gm_week():
    workspaces = get_workspaces()
    for workspace in workspaces:
        print("Running gm_week for " + workspace["team_id"])
        db = DatabaseWrapper(workspace["team_id"])

        if db.season:
            champion = db.get_last_weeks_winner()
            text = f"Congratulations to <@{champion}> for getting the most points this week!"

            post_message(text, workspace["channel"], workspace["oauth"])
