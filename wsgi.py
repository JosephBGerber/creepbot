from snapshot import app as application
from snapshot.scheduler import setup_jobs

if __name__ == '__main__':
    setup_jobs()
    application.run(host="0.0.0.0", port="8080")
