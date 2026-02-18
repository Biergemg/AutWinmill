import pandas as pd
import json
import os
import sys
from datetime import datetime

RESULTS_DIR = "ops/benchmarks/results"
SUMMARY_FILE = os.path.join(RESULTS_DIR, "latest-summary.md")
JSON_SUMMARY = os.path.join(RESULTS_DIR, "latest-summary.json")

def generate_report():
    print("Generating Benchmark Report...")
    
    # Ensure results dir exists
    if not os.path.exists(RESULTS_DIR):
        print(f"Directory {RESULTS_DIR} not found.")
        return

    # Locate Locust CSVs
    stats_file = None
    for f in os.listdir(RESULTS_DIR):
        if f.endswith("_stats.csv"):
            stats_file = os.path.join(RESULTS_DIR, f)
            break
            
    stats_data = {}
    if stats_file:
        try:
            df = pd.read_csv(stats_file)
            # Locust csv format: Type, Name, Request Count, Failure Count, Median Response Time, ..., Average Response Time, ...
            # We want overall Aggregated row
            overall = df[df["Name"] == "Aggregated"]
            if not overall.empty:
                stats_data = overall.iloc[0].to_dict()
        except Exception as e:
            print(f"Error reading CSV: {e}")

    # Cost Estimation Model (simple)
    # Assume $0.00001 per 100ms of execution (just an example metric)
    req_count = stats_data.get("Request Count", 0)
    avg_time_ms = stats_data.get("Average Response Time", 0)
    
    # 1000 executions cost
    cost_per_1k = (avg_time_ms / 100) * 0.00001 * 1000
    
    report = f"""# Benchmark Summary
**Date:** {datetime.now().isoformat()}

## Load Test Results
- **Total Requests:** {req_count}
- **Failures:** {stats_data.get("Failure Count", 0)}
- **RPS:** {stats_data.get("Requests/s", 0)}
- **Latency (Avg):** {avg_time_ms:.2f} ms
- **Latency (p95):** {stats_data.get("95%", 0)} ms
- **Latency (p99):** {stats_data.get("99%", 0)} ms

## Cost Estimation (Projected)
- **Cost per 1k Executions:** ${cost_per_1k:.5f}
*(Based on simple model: $0.00001 per 100ms)*

## Status
{'✅ PASS' if stats_data.get("Failure Count", 0) == 0 else '❌ FAIL'}

"""
    
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(report)
        
    with open(JSON_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2)
        
    print(f"Report generated at {SUMMARY_FILE}")

if __name__ == "__main__":
    generate_report()
