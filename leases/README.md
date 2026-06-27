# Lease Documents

Drop your lease documents here to analyze them.

## Supported formats
- `.txt` — plain text (paste lease text, save as .txt)
- `.pdf` — PDF files (requires pypdf, already installed)

## How to analyze
```bash
# Analyze all leases in this folder
uv run python agent.py --dir leases/

# Analyze a specific lease
uv run python agent.py leases/my-lease.txt

# Analyze multiple specific files
uv run python agent.py leases/lease1.txt leases/lease2.txt
```

## Tips
- For PDFs: copy-paste the text into a .txt file for best results with local model
- Name files descriptively: `123-main-st-lease.txt`, `office-sublease.txt`
- Results are saved to logs/runs.jsonl after each run
