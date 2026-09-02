# pyMCUTracker

A family MCU movie watch tracker for the road to **Avengers: Doomsday**.

## Version 1 features

- Streamlit application with a cinematic superhero-inspired theme
- 40-title MCU movie catalog organized by phase and release order
- SQLiteCloud persistence
- Family account signup, login, and logout
- bcrypt password hashing
- First-created account automatically becomes administrator
- Personal watched-movie checklist
- Shared family progress tracker
- Backend authorization so members can only edit their own movie status
- Dashboard with personal, family, and phase progress
- Next-family-movie and watch-tonight recommendations
- Searchable movie library
- Administrator family management
- Activate/deactivate family accounts without deleting watch history
- Administrator-assisted password reset
- Automated tests for authentication, authorization, and recommendation logic
- Friendly database connection error handling

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/skeeven/pyMCUTracker.git
cd pyMCUTracker
```

### 2. Create a virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
```

### 4. Configure SQLiteCloud

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then replace the placeholder with the real SQLiteCloud connection string:

```text
SQLITECLOUD_URL=your-real-sqlitecloud-connection-string
```

Never commit `.env`, API keys, passwords, or `.streamlit/secrets.toml`.

### 5. Initialize the database

```bash
python -m database.schema
```

The initializer is safe to run more than once. Movie seeding uses `INSERT OR IGNORE`.

### 6. Run the app

```bash
streamlit run app.py
```

Create the first account through the app. The first account automatically becomes the administrator.

## Run the tests

```bash
pytest
```

A successful Version 1 test run should collect the authentication, authorization, and recommendation tests with no failures.

## Deploy to Streamlit Community Cloud

The application is designed to deploy directly from this GitHub repository.

1. Sign in to Streamlit Community Cloud and connect the GitHub account that owns this repository.
2. If the repository is private, grant Community Cloud access to private repositories.
3. Create a new app and select:
   - Repository: `skeeven/pyMCUTracker`
   - Branch: `main`
   - Main file path: `app.py`
4. Open **Advanced settings** before deploying.
5. Add the SQLiteCloud connection string to the **Secrets** field using TOML syntax:

```toml
SQLITECLOUD_URL = "your-real-sqlitecloud-connection-string"
```

6. Use a supported Python version. Python 3.12 is a conservative production choice for the current dependency stack.
7. Deploy the application.
8. Open the deployed URL and verify login, database access, movie updates, and administrator controls.

Do not add the production SQLiteCloud connection string to GitHub. Streamlit Community Cloud stores application secrets separately from the repository.

## Production verification checklist

Before sharing the URL with the family, verify:

- The app starts without database or dependency errors.
- The existing administrator can sign in.
- A second family member can create an account and sign in.
- A member can update only their own watched movies.
- Another member's Family Tracker column remains read-only.
- Movie progress persists after logout and login.
- Dashboard counts and recommendations update after movie changes.
- Deactivated accounts disappear from active family progress but retain history when reactivated.
- Administrator password reset works for another account.
- A normal member cannot access administrator controls.
- The app is usable on both desktop and mobile-sized screens.

## Project structure

```text
pyMCUTracker/
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── README.md
├── .env.example
├── auth/
│   ├── __init__.py
│   ├── service.py
│   └── ui.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.py
│   ├── user_movies.py
│   └── users.py
├── data/
│   └── movies.py
├── services/
│   └── recommendations.py
├── tests/
├── ui/
│   └── theme.py
└── views/
    ├── admin.py
    ├── family_tracker.py
    ├── movie_library.py
    └── my_movies.py
```

## Possible Version 2 additions

- Self-service email password reset
- Ratings and favorites
- Watched-together tracking
- TV / Disney+ series tracking
- Exact release dates, runtimes, posters, and synopsis data
- Additional recommendation modes
- Watch history and completion dates
