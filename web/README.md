# Web Dashboard

A simple web dashboard for viewing cryptic crossword evaluation results.

## Features

- **Results Table**: Ranked list of all evaluated models with accuracy, samples, and metadata
- **Accuracy Chart**: Bar chart with error bars showing model performance
- **Responsive Design**: Works on desktop and mobile devices

## Local Development

### Preview the dashboard locally

1. Build the results data:
   ```bash
   uv run python web/build_results.py
   ```

2. Start a local server:
   ```bash
   # Using Python's built-in server
   cd web && python -m http.server 8000
   ```

3. Open http://localhost:8000 in your browser

### Rebuild after new evaluations

After running new evaluations with `run_and_save.py`, rebuild the results:

```bash
uv run python web/build_results.py
```

## Deployment

The dashboard is automatically deployed to GitHub Pages when changes are pushed to main.

### Automatic deployment (GitHub Actions)

The workflow at `.github/workflows/deploy-pages.yml`:
1. Triggers on pushes to main that modify `results/` or `web/` files
2. Builds `results.json` from the JSONL files
3. Deploys the `web/` directory to GitHub Pages

### Manual deployment

To manually trigger deployment:
1. Go to Actions tab in GitHub
2. Select "Deploy to GitHub Pages" workflow
3. Click "Run workflow"

### First-time setup

To enable GitHub Pages for your repository:

1. Go to repository Settings > Pages
2. Under "Build and deployment", select:
   - Source: **GitHub Actions**
3. Push changes to main to trigger the first deployment

The site will be available at: `https://<username>.github.io/<repo-name>/`

## File Structure

```
web/
├── index.html        # Main HTML page
├── style.css         # Styles
├── app.js            # JavaScript for loading data and rendering
├── build_results.py  # Script to generate results.json
├── results.json      # Generated data (not tracked in git)
└── README.md         # This file
```

## Customization

### Modify the description

Edit the `<section class="abstract">` in `index.html` to update the benchmark description.

### Change styling

Edit `style.css` to customize colors, fonts, and layout. The CSS uses CSS variables for easy theming:

```css
:root {
    --primary-color: #2563eb;
    --text-color: #1f2937;
    /* ... */
}
```

### Add new metrics

1. Update `build_results.py` to include new fields in the result objects
2. Update `app.js` to display the new fields in the table
3. Update `index.html` table headers if needed
