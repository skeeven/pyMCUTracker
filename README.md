# pyMCUTracker

A family MCU movie watch tracker for the road to **Avengers: Doomsday**.

## Current milestone

Milestone 3 adds real family accounts backed by SQLiteCloud.

Completed:

- Streamlit application shell and cinematic theme
- 40-title MCU movie catalog
- SQLiteCloud schema and movie seeding
- Family account creation
- bcrypt password hashing
- Login and logout
- Authenticated Streamlit session state
- First-created account automatically becomes administrator

## Planned features

- Personal movie checklist
- Shared family progress matrix
- Only the logged-in user can edit their own watched status
- Progress bars and completion percentages
- Next-family-movie recommendations
- Administrator tools
- Streamlit Community Cloud deployment

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

### 4. Configure SQLiteCloud

Copy `.env.example` to `.env` and set your real connection string:

```text
SQLITECLOUD_URL=your-sqlitecloud-connection-string
```

Never commit the real `.env` file.

### 5. Initialize the database

```bash
python3 -m database.schema
```

The initializer is safe to run again; the movie seed uses `INSERT OR IGNORE`.

### 6. Run the app

```bash
streamlit run app.py
```

Create the first account through the app. The first account is automatically
marked as the administrator.

## Project structure

```text
pyMCUTracker/
├── app.py
├── requirements.txt
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
│   └── users.py
├── data/
│   └── movies.py
├── pages/
└── ui/
    └── theme.py
```
