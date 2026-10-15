# JobTrack: Job Application Tracker

A simple web app for tracking job applications, built with Python, Flask and MySQL.

## Features

- Add a job application (company, title, location, job link, date, status, notes)
- View all saved applications
- Edit an application
- Delete an application, with a confirmation popup
- Change status: Applied, Interview, Offer or Rejected
- Search by company name or job title
- Dashboard with total applications and a count for each status

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL (mysql-connector-python, parameterized queries)
- **Frontend:** HTML, CSS, Bootstrap 5, Jinja2

## Project Structure

```
JobTrack/
├── app.py              # Flask routes and form validation
├── config.py           # Reads settings from .env
├── db.py               # MySQL connection helpers
├── requirements.txt
├── schema.sql          # Creates the database and table
├── .env.example        # Template for your settings
├── .gitignore
├── README.md
├── templates/          # base, dashboard, applications, application_form, error
└── static/css/style.css
```

## Setup (Windows 11)

**Requirements:** Python 3.9+, MySQL Server 8.x, VS Code, Git.

1. Clone the repository and open the folder in VS Code:
```
   git clone https://github.com/bhupeshsaini7/JobTrack.git
   cd JobTrack
```
2. Create a virtual environment and install packages:
```
   python -m venv venv
   venv\Scripts\Activate.ps1
   pip install -r requirements.txt
```
3. Create the database and table (safe to run again, it never deletes data):
```
   mysql -u root -p -e "source schema.sql"
```
4. Create a limited MySQL user for the app (choose your own password):
```sql
   CREATE USER 'jobtrack_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON jobtrack.* TO 'jobtrack_user'@'localhost';
```
5. Create your `.env` file and fill in the values:
```
   copy .env.example .env
```
6. Run the app and open http://127.0.0.1:5000:
```
   python app.py
```

## Testing Checklist

1. Dashboard shows 0 for everything on an empty database.
2. Add an application: it appears in Applications and the dashboard counts update.
3. Submit the form with a blank company name, a bad link or a future date: an error is shown.
4. Edit an application and save: the changes appear.
5. Change the status from the dropdown: the status and dashboard counts update.
6. Search by company and by job title: only matching rows are shown.
7. Delete an application: a popup asks for confirmation, then it is removed.

## Known Limitations

- No login or user accounts (anyone who can open the app sees all data)
- No CSRF protection (Flask-WTF would add it)
- Runs in debug mode for local use; not set up for production

## Future Improvements

- User login
- Filter by status
- Sort by column
- Export to CSV

## Security

Secrets live in `.env`, which is excluded by `.gitignore`. Never upload it. All SQL uses parameterized queries.