# Simple DB Viewer (db_visualizer)

Start:
  npm install
  node server.js --host 0.0.0.0

Notes:
- This environment had issues resolving express's internal lib path in certain npm installs. 
- server.js includes a defensive fallback that resolves express via its package main entry if the default require fails.
- If you still encounter a module error, run: npm ci (if lockfile present) or remove node_modules and reinstall (manually).
