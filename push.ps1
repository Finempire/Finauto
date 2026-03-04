# push.ps1 — Quick push to GitHub
# Usage: .\push.ps1 "your commit message"
param(
    [string]$Message = "Update"
)

git add -A
git commit -m $Message
git push origin master
