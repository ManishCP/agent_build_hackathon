"""
frontend/app.py — Simple Flask web frontend for the Lease Analyzer Agent
Run: uv run python frontend/app.py
Then open: http://localhost:5001
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request

app = Flask(__name__)

# Root of the project (one level up from frontend/)
PROJECT_ROOT = Path(__file__).parent.parent

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lease Analyzer — TOA Agent Build Day 2026</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f5f0; color: #1a1a18; min-height: 100vh; }
    .header { background: #1a1a18; color: white; padding: 1.5rem 2rem;
              display: flex; align-items: center; gap: 12px; }
    .header h1 { font-size: 1.2rem; font-weight: 500; }
    .header .sub { font-size: 0.8rem; color: #888; margin-top: 2px; }
    .badge { background: #2a2a28; border: 1px solid #444; border-radius: 20px;
             padding: 3px 10px; font-size: 11px; color: #aaa; }
    .container { max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; }
    .card { background: white; border: 1px solid #e5e5e0; border-radius: 12px;
            padding: 1.5rem; margin-bottom: 1.5rem; }
    .card h2 { font-size: 1rem; font-weight: 500; margin-bottom: 1rem; color: #1a1a18; }
    textarea { width: 100%; height: 220px; padding: 12px; border: 1px solid #ddd;
               border-radius: 8px; font-family: monospace; font-size: 12px;
               resize: vertical; background: #fafaf8; }
    textarea:focus { outline: none; border-color: #555; }
    .btn { display: inline-block; padding: 10px 24px; background: #1a1a18;
           color: white; border: none; border-radius: 8px; font-size: 14px;
           cursor: pointer; transition: opacity .15s; }
    .btn:hover { opacity: 0.85; }
    .btn-outline { background: transparent; border: 1px solid #ccc; color: #444;
                   text-decoration: none; }
    .btn-outline:hover { background: #f5f5f0; opacity: 1; }
    .options { display: flex; gap: 1rem; align-items: center; margin-top: 1rem; flex-wrap: wrap; }
    label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #555; cursor: pointer; }
    input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
    input[type=file] { font-size: 13px; color: #555; }
    .result-box { background: #1a1a18; color: #e0e0d8; border-radius: 10px;
                  padding: 1.25rem 1.5rem; font-family: monospace; font-size: 12px;
                  line-height: 1.8; white-space: pre-wrap; overflow-x: auto; }
    .score-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
                  margin: 0 0 1rem 0; }
    .score-card { border-radius: 10px; padding: 1rem; text-align: center; border: 1px solid transparent; }
    .score-card .num { font-size: 2rem; font-weight: 600; line-height: 1; }
    .score-card .lbl { font-size: 11px; color: #666; margin-top: 4px;
                       text-transform: uppercase; letter-spacing: .05em; }
    .risk-red { background: #fef2f2; border-color: #fca5a5; }
    .risk-red .num { color: #dc2626; }
    .risk-yel { background: #fffbeb; border-color: #fcd34d; }
    .risk-yel .num { color: #d97706; }
    .risk-grn { background: #f0fdf4; border-color: #86efac; }
    .risk-grn .num { color: #16a34a; }
    .risk-neu { background: #f8f8f6; border-color: #e5e5e0; }
    .risk-neu .num { color: #555; }
    .history-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .history-table th { text-align: left; padding: 8px 12px; border-bottom: 2px solid #e5e5e0;
                        color: #888; font-weight: 500; font-size: 11px; text-transform: uppercase; }
    .history-table td { padding: 8px 12px; border-bottom: 1px solid #f0f0ec; color: #444; }
    .history-table tr:hover td { background: #fafaf8; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 20px;
           font-size: 10px; font-weight: 500; }
    .tag-red { background: #fef2f2; color: #dc2626; }
    .tag-yel { background: #fffbeb; color: #d97706; }
    .tag-grn { background: #f0fdf4; color: #16a34a; }
    .empty { text-align: center; color: #aaa; padding: 2rem; font-size: 13px; }
    .meta { font-size: 11px; color: #999; margin-top: 8px; }
    .divider { height: 1px; background: #e5e5e0; margin: 1rem 0; }
    .spinner { display: none; }
    form:not(.idle) .btn[type=submit] { opacity: 0.6; pointer-events: none; }
  </style>
</head>
<body>

<div class="header">
  <div>
    <h1>Lease Analyzer Agent</h1>
    <div class="sub">TOA Agent Build Day 2026 · Lane 1</div>
  </div>
  <span class="badge">granite4:micro</span>
  <span class="badge">4 skills</span>
</div>

<div class="container">

  <div class="card">
    <h2>Analyze a lease</h2>
    <form method="POST" action="/analyze" enctype="multipart/form-data">
      <textarea name="lease_text" placeholder="Paste your commercial lease text here...

Example: NNN lease at $8,500/month, 4% annual escalation, personal guarantee
required, 60-day auto-renewal, holdover at 200%...">{{ prefill or '' }}</textarea>

      <div class="divider"></div>

      <div style="margin-bottom:.75rem">
        <input type="file" name="lease_file" accept=".txt,.pdf">
        <div class="meta">Upload a .txt or .pdf lease document</div>
      </div>

      <div class="options">
        <button type="submit" class="btn">Analyze lease</button>
        <label>
          <input type="checkbox" name="no_skill" value="1"> Baseline (no skill)
        </label>
        <label>
          <input type="checkbox" name="frontier" value="1"> Use Claude Sonnet
        </label>
        <a href="/sample" class="btn btn-outline">Load sample lease</a>
      </div>
    </form>
  </div>

  {% if result %}
  <div class="card">
    <h2>Analysis result</h2>

    {% if scores %}
    <div class="score-grid">
      <div class="score-card {{ score_class(scores.financial) }}">
        <div class="num">{{ scores.financial if scores.financial is not none else '—' }}</div>
        <div class="lbl">Financial</div>
      </div>
      <div class="score-card {{ score_class(scores.clauses) }}">
        <div class="num">{{ scores.clauses if scores.clauses is not none else '—' }}</div>
        <div class="lbl">Clauses</div>
      </div>
      <div class="score-card {{ score_class(scores.exit) }}">
        <div class="num">{{ scores.exit if scores.exit is not none else '—' }}</div>
        <div class="lbl">Exit</div>
      </div>
      <div class="score-card {{ score_class(scores.overall) }}">
        <div class="num">{{ scores.overall if scores.overall is not none else '—' }}</div>
        <div class="lbl">Overall</div>
      </div>
    </div>
    {% endif %}

    <div class="result-box">{{ result }}</div>
    {% if meta %}
    <div class="meta">{{ meta }}</div>
    {% endif %}
  </div>
  {% endif %}

  <div class="card">
    <h2>Run history</h2>
    {% if history %}
    <table class="history-table">
      <thead>
        <tr>
          <th>Time</th><th>File</th><th>Model</th><th>Skill</th>
          <th>Financial</th><th>Clauses</th><th>Exit</th>
          <th>Overall</th><th>Latency</th>
        </tr>
      </thead>
      <tbody>
        {% for row in history %}
        <tr>
          <td>{{ row.time }}</td>
          <td>{{ row.filename }}</td>
          <td>{{ row.model }}</td>
          <td>{{ "Yes" if row.skill_used else "No" }}</td>
          <td>{{ row.financial_score if row.financial_score is not none else "—" }}</td>
          <td>{{ row.clause_score   if row.clause_score   is not none else "—" }}</td>
          <td>{{ row.exit_score     if row.exit_score     is not none else "—" }}</td>
          <td>
            {% if row.overall_score is not none %}
              {% if row.overall_score >= 70 %}
                <span class="tag tag-grn">{{ row.overall_score }} Low</span>
              {% elif row.overall_score >= 40 %}
                <span class="tag tag-yel">{{ row.overall_score }} Med</span>
              {% else %}
                <span class="tag tag-red">{{ row.overall_score }} High</span>
              {% endif %}
            {% else %}—{% endif %}
          </td>
          <td>{{ row.latency }}s</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty">No runs yet — analyze a lease to see history here.</div>
    {% endif %}
  </div>

</div>
</body>
</html>
"""


def score_class(score):
    if score is None:
        return "risk-neu"
    if score >= 70:
        return "risk-grn"
    if score >= 40:
        return "risk-yel"
    return "risk-red"


def load_history():
    log_path = PROJECT_ROOT / "logs" / "runs.jsonl"
    if not log_path.exists():
        return []
    rows = []
    for line in log_path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            entry["time"] = entry.get("timestamp", "")[:16].replace("T", " ")
            entry["filename"] = Path(entry.get("filename", "unknown")).name
            entry["latency"] = round(entry.get("latency_seconds") or 0, 1)
            rows.append(entry)
        except Exception:
            continue
    return list(reversed(rows))


def extract_scores_from_log() -> dict:
    """Read the most recent run from logs/runs.jsonl for score display."""
    log_path = PROJECT_ROOT / "logs" / "runs.jsonl"
    if not log_path.exists():
        return {}
    lines = [l for l in log_path.read_text().strip().split("\n") if l.strip()]
    if not lines:
        return {}
    try:
        entry = json.loads(lines[-1])
        scores = {
            "financial": entry.get("financial_score"),
            "clauses":   entry.get("clause_score"),
            "exit":      entry.get("exit_score"),
            "overall":   entry.get("overall_score"),
        }
        return scores
    except Exception:
        return {}


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        result=None, scores=None, meta=None,
        history=load_history(), prefill=None,
        score_class=score_class,
    )


@app.route("/sample")
def load_sample():
    sample = PROJECT_ROOT / "evals" / "files" / "sample_lease.txt"
    text = sample.read_text() if sample.exists() else ""
    return render_template_string(
        HTML_TEMPLATE,
        result=None, scores=None, meta=None,
        history=load_history(), prefill=text,
        score_class=score_class,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    lease_text = request.form.get("lease_text", "").strip()
    lease_file = request.files.get("lease_file")
    no_skill   = request.form.get("no_skill") == "1"
    frontier   = request.form.get("frontier") == "1"

    leases_dir = PROJECT_ROOT / "leases"
    leases_dir.mkdir(exist_ok=True)

    if lease_file and lease_file.filename:
        tmp_path = leases_dir / lease_file.filename
        lease_file.save(str(tmp_path))
        cmd_input = str(tmp_path)
    elif lease_text:
        tmp_path = leases_dir / "_pasted_text.txt"
        tmp_path.write_text(lease_text)
        cmd_input = str(tmp_path)
    else:
        cmd_input = str(PROJECT_ROOT / "evals" / "files" / "sample_lease.txt")

    cmd = [sys.executable, "agent.py", cmd_input]
    if no_skill:
        cmd.append("--no-skill")
    if frontier:
        cmd.append("--frontier")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[stderr: {proc.stderr}]"
    except subprocess.TimeoutExpired:
        output = "[Error: agent timed out after 5 minutes]"
    except Exception as e:
        output = f"[Error running agent: {e}]"

    scores = extract_scores_from_log()

    meta = ""
    for line in output.split("\n"):
        if "turns=" in line and "latency=" in line:
            meta = line.strip()
            break

    return render_template_string(
        HTML_TEMPLATE,
        result=output,
        scores=scores if any(v is not None for v in scores.values()) else None,
        meta=meta,
        history=load_history(),
        prefill=None,
        score_class=score_class,
    )


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Lease Analyzer — Web Frontend")
    print("Open: http://localhost:5001")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5001)
