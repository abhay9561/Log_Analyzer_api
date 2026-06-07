"""
generate_sample_log.py
======================
Generates a realistic CSV log file for testing the Log Analyzer API.

Usage:
    python generate_sample_log.py          # generates 1000 lines (default)
    python generate_sample_log.py 5000     # generates 5000 lines

Output:
    sample_logs/test.log

Log Format:
    <timestamp>,<user_id>,<amount>,<log_level>,<message>

Example lines:
    2024-01-01 08:00:00,user_0042,15000.00,ERROR,Payment gateway timeout
    2024-01-01 08:00:03,user_0010,500.00,INFO,Login successful
"""

import random
import sys
from datetime import datetime, timedelta

# ── Config ───────────────────────────────────────────────────────────────────
USERS = [f"user_{i:04d}" for i in range(1, 101)]

LOG_LEVELS = ["INFO", "DEBUG", "WARNING", "ERROR"]
LEVEL_WEIGHTS = [50, 20, 15, 15]   # INFO most common, ERROR least

MESSAGES = [
    "Payment gateway timeout",
    "Duplicate transaction detected",
    "Login successful",
    "Session expired",
    "Retry limit exceeded",
    "Database write failure",
    "Auth token invalid",
    "Rate limit hit",
    "Transfer complete",
    "Reconciliation mismatch",
    "Account balance updated",
    "Fraud detection triggered",
]

OUTPUT_PATH = "sample_logs/test.log"


# ── Generator ─────────────────────────────────────────────────────────────────
def generate_log(num_lines: int = 1000, output_path: str = OUTPUT_PATH) -> None:
    """
    Write num_lines of random log data to output_path.
    Uses a context manager (with open) — safe file handling.
    """
    base_time = datetime(2024, 1, 1, 8, 0, 0)

    with open(output_path, "w", encoding="utf-8") as f:
        for i in range(num_lines):
            timestamp = (base_time + timedelta(seconds=i * 3)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            user    = random.choice(USERS)
            amount  = round(random.uniform(100.0, 50_000.0), 2)
            level   = random.choices(LOG_LEVELS, weights=LEVEL_WEIGHTS)[0]
            message = random.choice(MESSAGES)

            f.write(f"{timestamp},{user},{amount},{level},{message}\n")

    print(f"✅  Generated {num_lines:,} lines  →  {output_path}")
    print(f"     (Roughly {num_lines * 0.15:.0f} lines will be ERROR level)")
    print(f"     (Roughly {num_lines * 0.15 * 0.5:.0f} lines will be flagged >$10,000)")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    generate_log(n)
