# Publishing the project on GitHub

## 1. Take screenshots first

Run the dashboard and save the screenshots listed in `README.md` into `docs/screenshots/` (Windows key + Shift + S, then save the image). Then add this section to the end of `README.md` using Notepad++:

```
## Screenshots

![Executive overview](docs/screenshots/01-executive-overview.png)
![Marketing performance](docs/screenshots/02-marketing-performance.png)
![Conversion funnel](docs/screenshots/03-conversion-funnel.png)
![Checkout and payments](docs/screenshots/04-checkout-payments.png)
```

## 2. Create the empty repository on GitHub

1. Sign in at github.com and click the **+** at the top right, then **New repository**.
2. **Repository name:** `performance-roi-conversion-analyzer`
3. **Description:** `Performance ROI & Conversion Drop-off Analyzer - SQL, Python and Streamlit analytics dashboard built on synthetic e-commerce data`
4. Choose **Public**.
5. Do **not** tick "Add a README", ".gitignore" or "license" (the project already has them).
6. Click **Create repository**.

## 3. Upload from PowerShell

Open PowerShell in the project folder (see `START_HERE_WINDOWS.md`, Step 2) and run these one at a time. Replace `YOUR-GITHUB-USERNAME` with your GitHub username.

```
git --version
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
git init
git add .
git commit -m "Initial commit: Performance ROI & Conversion Drop-off Analyzer"
git branch -M main
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/performance-roi-conversion-analyzer.git
git push -u origin main
```

If `git` is not recognised, install Git for Windows from git-scm.com, accept the defaults, and reopen PowerShell.

A browser window may ask you to sign in to GitHub the first time you push. Approve it.

**You should see:** `Branch 'main' set up to track 'origin/main'.` Refresh the GitHub page and your files appear, with the README shown below the file list.

## 4. Final checks

- The README shows the synthetic-data notice near the top.
- The `data` folder is included, so others can run the dashboard right after installing requirements.
- The repository name and description use the exact project name.
