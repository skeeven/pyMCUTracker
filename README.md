# pyMCUTracker

A family MCU movie watch tracker for the road to **Avengers: Doomsday**.

## Current milestone

Milestone 1 establishes the Streamlit application shell, visual theme, and the
initial 40-title movie catalog.

## Planned features

- Family signup and login
- Personal movie checklist
- Shared family progress matrix
- Only the logged-in user can edit their own watched status
- Progress bars and completion percentages
- Next-family-movie recommendations
- SQLiteCloud persistence
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

### 4. Run the app

```bash
streamlit run app.py
```

Streamlit should open the application in your browser automatically.

## Project structure

```text
pyMCUTracker/
├── app.py
├── requirements.txt
├── README.md
├── auth/
├── database/
├── data/
│   └── movies.py
├── pages/
└── ui/
    └── theme.py
```

Additional modules will be added as each milestone is implemented.
