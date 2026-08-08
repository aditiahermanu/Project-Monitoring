# Project Monitoring Web Application

Web-based, multi-user Flask application. Users only need a browser after deployment.

Dashboard covers: Project Status, Progress, Budget, Schedule, Risk, Issue, Action Tracker and PIC.

Roles:
- admin: user management
- project_user: create/manage projects
- executor: update projects assigned as PIC

Demo accounts:
admin / Admin123!
project / Project123!
executor / Executor123!

Deploy: GitHub -> Render Web Service; Build `pip install -r requirements.txt`; Start `gunicorn app:app`; set SECRET_KEY and production DATABASE_URL (PostgreSQL recommended).

Docker: `docker build -t project-monitoring .` then `docker run -p 5000:5000 project-monitoring`

Change demo passwords before production. Add HTTPS and database backups.
