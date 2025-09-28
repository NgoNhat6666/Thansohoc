Thần Số Học – Static Site (GitHub Pages)

This repository hosts a fully static, client‑side numerology (Thần Số Học) website designed to be deployed on GitHub Pages.

What’s inside
- docs/index.html – main site (Vietnamese UI)
- docs/assets/styles.css – modern responsive styles
- docs/assets/app.js – client‑side numerology logic (Life Path, Expression, Soul Urge, Personality basics)
- docs/404.html – SPA fallback for GitHub Pages
- .github/workflows/pages.yml – auto‑deploy to GitHub Pages from the docs folder

Local preview
You can serve the site locally with any static server. For example:

```bash
python3 -m http.server 5500 -d docs
```

Then open http://localhost:5500

Deploy to GitHub Pages
Option A (recommended – branch gh-pages):
1) Push changes to main.
2) Workflow gh-pages.yml publishes docs/ to the gh-pages branch.
3) In Settings → Pages, set Source = Deploy from a branch, Branch = gh-pages / (root).
4) Your site url: https://<username>.github.io/Thansohoc/

Option B (Pages build & deploy):
If you prefer the official pages workflow (pages.yml), ensure the repository has Pages enabled for GitHub Actions. If Setup Pages step fails, switch to Option A.

Notes
- The previous FastAPI backend has been removed from the deployable surface. All calculations are now done on the client.
- If you still have large folders locally (e.g., numerus-starter-v16 or zip files), they are intentionally left untracked so they won’t be published. You can safely delete them locally.
# Thansohoc