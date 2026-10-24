# Start Here (Windows, beginner guide)

Follow these steps in order. After each step, check that your result looks like the "You should see" line before continuing. If it doesn't, copy the exact error message and ask for help.

## Step 1: Put the project in a folder

1. Download the project zip, right-click it, choose **Extract All...**, and extract it to `C:\Users\<your name>\Documents`.
2. You should now have a folder named `performance-roi-conversion-analyzer` with files like `app.py` inside.

**You should see:** `app.py`, `README.md`, `requirements.txt` and folders `data`, `sql`, `docs` in File Explorer.

## Step 2: Open PowerShell inside that folder

1. In File Explorer, open the project folder.
2. Click the **address bar** at the top (where the folder path is shown), type `powershell`, and press **Enter**.

**You should see:** a PowerShell window whose prompt ends with `...\performance-roi-conversion-analyzer>`.

## Step 3: Check Python

Run:

```
python --version
```

**You should see:** `Python 3.11.x` or newer (3.12, 3.13 and so on are fine).
If you see "not recognized" or the Microsoft Store opens, install Python from python.org and **tick "Add python.exe to PATH"**, then close and reopen PowerShell. If `python` still fails, try `py --version` and use `py` instead of `python` in every command below.

## Step 4: Install the libraries

Run:

```
python -m pip install -r requirements.txt
```

**You should see:** a list of downloads ending with `Successfully installed ...` (it may take 1 to 3 minutes).

## Step 5: Create the data and the database

Run these one at a time:

```
python generate_data.py
python build_database.py
python validate_data.py
python test_project.py
```

**You should see:**
- `Created ...campaigns.csv (48 campaigns)` and `Created ...payments.csv (15 ...)`
- `Created ...analytics.db` with 48 and 15 rows
- `All validation checks passed.`
- `All 7 tests passed.`

## Step 6: Look at the SQL answers

```
python run_queries.py
```

**You should see:** seven result tables, Q1 to Q7. Open `sql\queries.sql` in Notepad++ to read the explanation of each query.

## Step 7: Start the dashboard

```
python -m streamlit run app.py
```

**You should see:** your browser opens `http://localhost:8501` showing "Performance ROI & Conversion Drop-off Analyzer". If Streamlit asks for an email in the terminal, just press Enter.

Try the **Market**, **Marketing channel** and **Campaign** filters in the left sidebar. The KPI cards and charts should change.

To stop the dashboard, click the PowerShell window and press **Ctrl + C**.

## Common problems

| Message | What to do |
|---|---|
| `'python' is not recognized` | Install Python with "Add to PATH", or use `py` |
| `No module named 'streamlit'` | Run Step 4 again |
| `Database not found` | Run `python generate_data.py` then `python build_database.py` |
| `streamlit is not recognized` | Use `python -m streamlit run app.py` |
| Port already in use | Close the old dashboard (Ctrl + C) or run `python -m streamlit run app.py --server.port 8502` |

## Next

Take the screenshots listed in `README.md`, then follow `docs/GITHUB_UPLOAD.md`.
