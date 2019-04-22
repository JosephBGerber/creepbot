from snapshot import app as application
from snapshot.scheduler import gm_week
from apscheduler.schedulers.background import BackgroundScheduler


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=gm_week, trigger="cron", week="*", day_of_week="6", hour="23", minute="0")
    scheduler.add_job(func=gm_week, trigger="cron", hour="*")
    scheduler.start()

    application.run(host="0.0.0.0", port="8080")
