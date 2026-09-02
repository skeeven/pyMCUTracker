# pyMCUTracker

A family Marvel movie watch tracker for the road to **Avengers: Doomsday**.

## Version 1 features

- Streamlit application with a cinematic superhero-inspired theme
- SQLiteCloud-backed movie catalog and family progress
- Original 40-title MCU catalog seeded automatically
- Supplemental/non-MCU Road to Doomsday titles supported
- Administrator movie management: add, edit, reorder, categorize, activate/deactivate
- Categories and universe/continuity metadata
- Family account signup, login, logout, and bcrypt password hashing
- First-created account automatically becomes administrator
- Personal watched-movie checklist
- Shared family progress tracker
- Backend authorization so members can only edit their own movie status
- Dashboard with personal, family, and section progress
- Next-family-movie and watch-tonight recommendations
- Searchable/filterable movie library
- Administrator family management and password reset
- Automated tests for authentication, authorization, and recommendation logic
- Automatic database schema migrations on app startup
- Friendly database connection error handling

## Movie catalog model

SQLiteCloud is the source of truth for the live movie list. `data/movies.py` remains only as the seed for the original MCU catalog.

Each catalog entry can store:

- Title
- Release year and optional exact release date
- MCU phase (`0` means Supplemental / non-MCU)
- Watch order
- Category
- Universe / continuity
- Core MCU flag
- Doomsday-relevant flag
- Active/inactive status
- Notes

Administrators can manage these fields from **Administration → Movies**. Inserting or moving a title to a watch-order position automatically shifts the surrounding titles. Deactivating a movie hides it from active progress while preserving existing family watch history.

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

Copy `.env.example` to `.env` and replace the placeholder with the real SQLiteCloud connection string:

```text
SQLITECLOUD_URL=your-real-sqlitecloud-connection-string
```

Never commit `.env`, API keys, passwords, or `.streamlit/secrets.toml`.

### 5. Run the app

```bash
streamlit run app.py
```

The app creates/migrates the schema and seeds missing original MCU titles once per application process. You can still run the migration directly when needed:

```bash
python -m database.schema
```

## Run the tests

```bash
pytest
```

## Deploy to Streamlit Community Cloud

1. Connect Streamlit Community Cloud to the GitHub account that owns this repository.
2. Select repository `skeeven/pyMCUTracker`, branch `main`, and main file `app.py`.
3. In **Advanced settings**, add the SQLiteCloud connection string to **Secrets**:

```toml
SQLITECLOUD_URL = "your-real-sqlitecloud-connection-string"
```

4. Python 3.12 is a conservative production choice for the current dependency stack.
5. Deploy and verify login, catalog access, progress updates, and administrator controls.

## Production verification checklist

Before sharing the URL with the family, verify:

- The app starts and automatically migrates the existing database.
- Existing accounts and watch history are unchanged.
- An administrator can add a Supplemental movie and place it anywhere in watch order.
- The new movie appears in My Movies, Family Tracker, Movie Library, dashboard totals, and recommendations.
- Reordering a movie shifts neighboring titles correctly.
- Deactivating a movie removes it from active progress without deleting watch history.
- A member can update only their own watched movies.
- Dashboard counts and recommendations update after movie changes.
- A normal member cannot access administrator controls.
- The app works on desktop and mobile-sized screens.

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
├── database/
│   ├── connection.py
│   ├── movies.py
│   ├── schema.py
│   ├── user_movies.py
│   └── users.py
├── data/
│   └── movies.py
├── services/
│   └── recommendations.py
├── tests/
├── ui/
└── views/
```

## Possible Version 2 additions

- Self-service email password reset
- Ratings and favorites
- Watched-together tracking
- TV / Disney+ series tracking
- Posters, runtimes, and synopsis data
- Additional recommendation modes
- Watch history and completion dates
