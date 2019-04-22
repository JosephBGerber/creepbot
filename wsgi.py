from snapshot import app as application
from snapshot.scheduler import gm_week
from apscheduler.schedulers.background import BackgroundScheduler


def test_cron():
    print("Work pls")


@application.before_first_request
def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=gm_week, trigger="cron", week="*", day_of_week="6", hour="23", minute="0")
    scheduler.add_job(func=test_cron, trigger="cron", second="*/5")
    scheduler.start()


if __name__ == '__main__':
    application.run(host="0.0.0.0", port="8080")
