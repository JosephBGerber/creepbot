from snapshot import app as application
from snapshot.scheduler import gm_week
from flask_apscheduler import APScheduler


class Config(object):
    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


@scheduler.task("cron", week="*", day_of_week="6", hour="23", minute="0")
def job():
    gm_week()


@scheduler.task("cron", second="*/10")
def job2():
    print("work please")


if __name__ == '__main__':
    application.config.from_object(Config())

    scheduler.init_app(application)
    scheduler.start()

    application.run(host="0.0.0.0", port="8080")
