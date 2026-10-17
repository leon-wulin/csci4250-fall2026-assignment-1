# Verified local setup

The user-confirmed project root is `H:\work_space\Frontiers_of_Network_Science\Assignment_1`. The existing environment is `fons-a1` with Python 3.12; it does not need to be recreated.

Open PowerShell and run the repeatable startup check:

```powershell
Set-Location 'H:\work_space\Frontiers_of_Network_Science\Assignment_1'
& .\scripts\preflight.ps1
```

The wrapper uses the verified `C:\ProgramData\anaconda3\Scripts\conda.exe` if `conda` is not on `PATH`. It requires no activation, environment creation, package installation, or persistent shell configuration. See README for setup on another machine.

The agent must use the named environment and validate `sys.executable` before trusting results. The verified interpreter is `C:\Users\lin\.conda\envs\fons-a1\python.exe`. See `PROJECT_STATUS.md` for measured versions and check results. Any package changes require the student's approval.
