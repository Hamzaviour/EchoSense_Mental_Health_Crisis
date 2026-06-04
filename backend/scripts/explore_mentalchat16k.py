"""
Explore and visualize the MentalChat16K dataset used for Echo Sense RAG ingestion.

Usage:
  python scripts/explore_mentalchat16k.py
  python scripts/explore_mentalchat16k.py --limit 500 --samples 5 --open

Outputs:
  backend/data/exploration/mentalchat16k_report.html
  backend/data/exploration/charts/*.png
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATASET_ID = "ShenLab/MentalChat16K"
COLUMNS = ("instruction", "input", "output")


def load_dataset(limit: int | None):
    from datasets import load_dataset

    token = os.getenv("HF_TOKEN")
    ds = load_dataset(DATASET_ID, token=token)
    split = ds["train"] if "train" in ds else list(ds.values())[0]
    if limit:
        split = split.select(range(min(limit, len(split))))
    return ds, split


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def safe_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value).strip()


TOPIC_KEYWORDS = (
    "anxiety",
    "depression",
    "grief",
    "stress",
    "relationship",
    "family",
    "burnout",
    "sleep",
    "panic",
    "trauma",
    "lonely",
    "suicid",
    "caregiver",
    "hospice",
    "medication",
    "therapy",
)


def topic_hint(row: dict) -> str:
    instruction = safe_text(row.get("instruction"))
    inp = safe_text(row.get("input"))
    haystack = f"{instruction} {inp}".lower()
    hits = [kw for kw in TOPIC_KEYWORDS if kw in haystack]
    if hits:
        return ", ".join(k.title() for k in hits[:3])
    if inp:
        return inp.split(".")[0][:100]
    if instruction:
        return instruction.split(".")[0][:100]
    return "(none)"


def row_stats(row: dict) -> dict:
    instruction = safe_text(row.get("instruction"))
    inp = safe_text(row.get("input"))
    out = safe_text(row.get("output"))
    combined = "\n".join(p for p in (instruction, inp, out) if p)
    return {
        "instruction_words": word_count(instruction),
        "input_words": word_count(inp),
        "output_words": word_count(out),
        "combined_words": word_count(combined),
        "combined_chars": len(combined),
        "has_instruction": bool(instruction),
        "has_input": bool(inp),
        "has_output": bool(out),
        "topic_hint": topic_hint(row),
    }


def build_summary(split) -> dict:
    rows = [row_stats(row) for row in split]
    n = len(rows) or 1

    def col_stats(key: str) -> dict:
        values = [r[key] for r in rows]
        return {
            "mean": round(mean(values), 1),
            "median": round(median(values), 1),
            "min": min(values),
            "max": max(values),
        }

    completeness = {
        col: round(100 * sum(1 for row in split if safe_text(row.get(col))) / n, 1)
        for col in COLUMNS
    }

    topics = Counter(r["topic_hint"] for r in rows if r["topic_hint"] != "(none)")

    keyword_hits: Counter[str] = Counter()
    for row in split:
        haystack = f"{safe_text(row.get('instruction'))} {safe_text(row.get('input'))}".lower()
        for kw in TOPIC_KEYWORDS:
            if kw in haystack:
                keyword_hits[kw] += 1

    return {
        "row_count": len(rows),
        "columns": list(split.column_names),
        "features": split.features if hasattr(split, "features") else {},
        "completeness_pct": completeness,
        "word_stats": {
            "instruction": col_stats("instruction_words"),
            "input": col_stats("input_words"),
            "output": col_stats("output_words"),
            "combined": col_stats("combined_words"),
        },
        "char_stats": col_stats("combined_chars"),
        "short_rows_lt_50_words": sum(1 for r in rows if r["combined_words"] < 50),
        "long_rows_gt_500_words": sum(1 for r in rows if r["combined_words"] > 500),
        "top_topics": topics.most_common(15),
        "keyword_hits": keyword_hits.most_common(),
        "rows": rows,
    }


def pick_samples(split, n: int) -> list[dict]:
    if len(split) == 0:
        return []
    step = max(1, len(split) // n)
    indices = [min(i * step, len(split) - 1) for i in range(n)]
    samples = []
    for idx in indices:
        row = split[int(idx)]
        samples.append(
            {
                "index": int(idx),
                "instruction": safe_text(row.get("instruction")),
                "input": safe_text(row.get("input")),
                "output": safe_text(row.get("output")),
            }
        )
    return samples


def print_summary(summary: dict, dataset_meta) -> None:
    print("\n=== MentalChat16K Dataset Exploration ===\n")
    print(f"Dataset:   {DATASET_ID}")
    print(f"Rows:      {summary['row_count']:,}")
    print(f"Columns:   {', '.join(summary['columns'])}")
    if dataset_meta:
        print(f"Splits:    {', '.join(dataset_meta.keys())}")

    print("\n--- Field completeness ---")
    for col, pct in summary["completeness_pct"].items():
        print(f"  {col:12} {pct:5.1f}%")

    print("\n--- Word count statistics ---")
    for field, stats in summary["word_stats"].items():
        print(
            f"  {field:12} mean={stats['mean']:7.1f}  "
            f"median={stats['median']:7.1f}  min={stats['min']:4d}  max={stats['max']:5d}"
        )

    print("\n--- Length flags ---")
    print(f"  Rows < 50 combined words:  {summary['short_rows_lt_50_words']}")
    print(f"  Rows > 500 combined words: {summary['long_rows_gt_500_words']}")

    if summary["top_topics"]:
        print("\n--- Top themes (keyword / client message hints) ---")
        for topic, count in summary["top_topics"][:10]:
            print(f"  [{count:4d}] {topic[:90]}")

    if summary.get("keyword_hits"):
        print("\n--- Mental health keyword frequency ---")
        for kw, count in summary["keyword_hits"][:10]:
            print(f"  {kw:14} {count}")


def print_samples(samples: list[dict]) -> None:
    print("\n=== Sample conversations ===\n")
    for sample in samples:
        print(f"--- Row #{sample['index']} ---")
        if sample["instruction"]:
            print(f"Instruction: {sample['instruction'][:200]}{'...' if len(sample['instruction']) > 200 else ''}")
        if sample["input"]:
            print(f"Client:      {sample['input'][:300]}{'...' if len(sample['input']) > 300 else ''}")
        if sample["output"]:
            print(f"Counselor:   {sample['output'][:300]}{'...' if len(sample['output']) > 300 else ''}")
        print()


def save_charts(summary: dict, chart_dir: Path) -> dict[str, str]:
    chart_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping charts (pip install matplotlib)")
        return paths

    rows = summary["rows"]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist([r["input_words"] for r in rows], bins=30, alpha=0.75, color="#0d9488", edgecolor="white")
    ax.set_title("Client message length (words)")
    ax.set_xlabel("Words")
    ax.set_ylabel("Count")
    fig.tight_layout()
    input_path = chart_dir / "input_word_hist.png"
    fig.savefig(input_path, dpi=120)
    plt.close(fig)
    paths["input_words"] = str(input_path)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist([r["output_words"] for r in rows], bins=30, alpha=0.75, color="#6366f1", edgecolor="white")
    ax.set_title("Counselor response length (words)")
    ax.set_xlabel("Words")
    ax.set_ylabel("Count")
    fig.tight_layout()
    output_path = chart_dir / "output_word_hist.png"
    fig.savefig(output_path, dpi=120)
    plt.close(fig)
    paths["output_words"] = str(output_path)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist([r["combined_words"] for r in rows], bins=30, alpha=0.75, color="#f59e0b", edgecolor="white")
    ax.set_title("Combined conversation length (words)")
    ax.set_xlabel("Words")
    ax.set_ylabel("Count")
    fig.tight_layout()
    combined_path = chart_dir / "combined_word_hist.png"
    fig.savefig(combined_path, dpi=120)
    plt.close(fig)
    paths["combined_words"] = str(combined_path)

    if summary["top_topics"]:
        top = summary["top_topics"][:10]
        labels = [t[:40] + ("…" if len(t) > 40 else "") for t, _ in top]
        counts = [c for _, c in top]
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(labels[::-1], counts[::-1], color="#14b8a6")
        ax.set_title("Top themes")
        ax.set_xlabel("Count")
        fig.tight_layout()
        topics_path = chart_dir / "top_topics.png"
        fig.savefig(topics_path, dpi=120)
        plt.close(fig)
        paths["top_topics"] = str(topics_path)

    if summary.get("keyword_hits"):
        kws = summary["keyword_hits"][:12]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar([k for k, _ in kws], [c for _, c in kws], color="#0ea5e9")
        ax.set_title("Mental health keyword frequency")
        ax.set_ylabel("Rows mentioning keyword")
        plt.xticks(rotation=35, ha="right")
        fig.tight_layout()
        kw_path = chart_dir / "keyword_freq.png"
        fig.savefig(kw_path, dpi=120)
        plt.close(fig)
        paths["keyword_freq"] = str(kw_path)

    return paths


def render_html(summary: dict, samples: list[dict], chart_paths: dict[str, str], output_path: Path) -> None:
    rel_charts = {k: os.path.relpath(v, output_path.parent).replace("\\", "/") for k, v in chart_paths.items()}

    def stat_cards() -> str:
        cards = [
            ("Rows analyzed", f"{summary['row_count']:,}"),
            ("Avg client words", f"{summary['word_stats']['input']['mean']}"),
            ("Avg counselor words", f"{summary['word_stats']['output']['mean']}"),
            ("Short rows (<50w)", str(summary["short_rows_lt_50_words"])),
        ]
        return "".join(
            f'<div class="card"><div class="card-label">{label}</div><div class="card-value">{value}</div></div>'
            for label, value in cards
        )

    def completeness_rows() -> str:
        return "".join(
            f"<tr><td>{col}</td><td>{pct}%</td></tr>"
            for col, pct in summary["completeness_pct"].items()
        )

    def word_stat_rows() -> str:
        rows_html = []
        for field, stats in summary["word_stats"].items():
            rows_html.append(
                f"<tr><td>{field}</td><td>{stats['mean']}</td>"
                f"<td>{stats['median']}</td><td>{stats['min']}</td><td>{stats['max']}</td></tr>"
            )
        return "".join(rows_html)

    def keyword_rows() -> str:
        if not summary.get("keyword_hits"):
            return "<tr><td colspan='2'>No keywords detected</td></tr>"
        return "".join(
            f"<tr><td>{html.escape(kw)}</td><td>{count}</td></tr>"
            for kw, count in summary["keyword_hits"]
        )

    def topic_rows() -> str:
        if not summary["top_topics"]:
            return "<tr><td colspan='2'>No topics detected</td></tr>"
        return "".join(
            f"<tr><td>{html.escape(topic)}</td><td>{count}</td></tr>"
            for topic, count in summary["top_topics"]
        )

    def chart_block(key: str, title: str) -> str:
        if key not in rel_charts:
            return ""
        return f"""
        <div class="chart-box">
          <h3>{html.escape(title)}</h3>
          <img src="{html.escape(rel_charts[key])}" alt="{html.escape(title)}" />
        </div>
        """

    def sample_cards() -> str:
        blocks = []
        for sample in samples:
            blocks.append(
                f"""
                <article class="sample">
                  <header>Row #{sample['index']}</header>
                  <div class="field"><span>Instruction</span><p>{html.escape(sample['instruction'] or '—')}</p></div>
                  <div class="field client"><span>Client</span><p>{html.escape(sample['input'] or '—')}</p></div>
                  <div class="field counselor"><span>Counselor</span><p>{html.escape(sample['output'] or '—')}</p></div>
                </article>
                """
            )
        return "".join(blocks)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MentalChat16K — Dataset Exploration</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #14b8a6;
      --accent2: #6366f1;
      --client: #38bdf8;
      --counselor: #a78bfa;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: linear-gradient(160deg, #0f172a 0%, #134e4a 100%);
      color: var(--text);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.75rem; }}
    .subtitle {{ color: var(--muted); margin-bottom: 1.5rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }}
    .card {{ background: var(--panel); border: 1px solid #334155; border-radius: 12px; padding: 1rem; }}
    .card-label {{ color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    .card-value {{ font-size: 1.6rem; font-weight: 700; color: var(--accent); margin-top: 0.25rem; }}
    section {{ background: rgba(30, 41, 59, 0.92); border: 1px solid #334155; border-radius: 14px; padding: 1.25rem; margin-bottom: 1.25rem; }}
    h2 {{ margin: 0 0 1rem; font-size: 1.1rem; color: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ text-align: left; padding: 0.55rem 0.65rem; border-bottom: 1px solid #334155; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
    .chart-box {{ background: #0b1220; border-radius: 10px; padding: 0.75rem; }}
    .chart-box img {{ width: 100%; height: auto; display: block; border-radius: 6px; }}
    .chart-box h3 {{ margin: 0 0 0.5rem; font-size: 0.95rem; color: var(--muted); }}
    .sample {{ background: #0b1220; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; }}
    .sample header {{ font-weight: 700; color: var(--accent2); margin-bottom: 0.75rem; }}
    .field span {{ display: inline-block; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); margin-bottom: 0.25rem; }}
    .field p {{ margin: 0 0 0.75rem; white-space: pre-wrap; }}
    .field.client span {{ color: var(--client); }}
    .field.counselor span {{ color: var(--counselor); }}
    code {{ background: #0b1220; padding: 0.15rem 0.35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>MentalChat16K Dataset Exploration</h1>
    <p class="subtitle">Echo Sense RAG source · Generated {generated_at}</p>

    <div class="cards">{stat_cards()}</div>

    <section>
      <h2>Schema</h2>
      <p>Columns: <code>{html.escape(", ".join(summary["columns"]))}</code></p>
      <p>Each row is a counselor–client exchange with an <code>instruction</code> (topic/context),
         <code>input</code> (client message), and <code>output</code> (counselor response).</p>
    </section>

    <section>
      <h2>Field completeness</h2>
      <table>
        <thead><tr><th>Column</th><th>Non-empty %</th></tr></thead>
        <tbody>{completeness_rows()}</tbody>
      </table>
    </section>

    <section>
      <h2>Word count statistics</h2>
      <table>
        <thead><tr><th>Field</th><th>Mean</th><th>Median</th><th>Min</th><th>Max</th></tr></thead>
        <tbody>{word_stat_rows()}</tbody>
      </table>
    </section>

    <section>
      <h2>Top themes</h2>
      <table>
        <thead><tr><th>Theme hint (keywords / client message)</th><th>Count</th></tr></thead>
        <tbody>{topic_rows()}</tbody>
      </table>
    </section>

    <section>
      <h2>Mental health keyword frequency</h2>
      <table>
        <thead><tr><th>Keyword</th><th>Rows</th></tr></thead>
        <tbody>{keyword_rows()}</tbody>
      </table>
    </section>

    <section>
      <h2>Distribution charts</h2>
      <div class="charts">
        {chart_block("input_words", "Client message length")}
        {chart_block("output_words", "Counselor response length")}
        {chart_block("combined_words", "Combined conversation length")}
        {chart_block("keyword_freq", "Keyword frequency")}
        {chart_block("top_topics", "Top themes")}
      </div>
    </section>

    <section>
      <h2>Sample conversations</h2>
      {sample_cards()}
    </section>
  </div>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")


def save_json_summary(summary: dict, output_path: Path) -> None:
    payload = {
        "dataset": DATASET_ID,
        "row_count": summary["row_count"],
        "columns": summary["columns"],
        "completeness_pct": summary["completeness_pct"],
        "word_stats": summary["word_stats"],
        "short_rows_lt_50_words": summary["short_rows_lt_50_words"],
        "long_rows_gt_500_words": summary["long_rows_gt_500_words"],
        "top_topics": summary["top_topics"],
        "keyword_hits": summary.get("keyword_hits", []),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Explore MentalChat16K dataset")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to analyze (default: full dataset)")
    parser.add_argument("--samples", type=int, default=6, help="Number of sample rows to show")
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "exploration"),
        help="Directory for HTML report and charts",
    )
    parser.add_argument("--open", action="store_true", help="Open HTML report in browser after generation")
    args = parser.parse_args()

    print(f"Loading {DATASET_ID} (limit={args.limit or 'all'})...")
    dataset, split = load_dataset(args.limit)
    summary = build_summary(split)
    samples = pick_samples(split, args.samples)

    print_summary(summary, dataset)
    print_samples(samples)

    output_dir = Path(args.output_dir).resolve()
    chart_dir = output_dir / "charts"
    report_path = output_dir / "mentalchat16k_report.html"
    json_path = output_dir / "mentalchat16k_summary.json"

    chart_paths = save_charts(summary, chart_dir)
    render_html(summary, samples, chart_paths, report_path)
    save_json_summary(summary, json_path)

    print(f"\nReport saved:  {report_path}")
    print(f"Summary JSON:  {json_path}")
    if chart_paths:
        print(f"Charts saved:  {chart_dir}")

    if args.open:
        webbrowser.open(report_path.as_uri())


if __name__ == "__main__":
    main()
