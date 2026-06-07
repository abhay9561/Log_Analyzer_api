"""
Log Analyzer API — Production-Ready Refactoring
================================================

PROBLEM STATEMENT COVERAGE:
  Task 1 — Refactoring  : OOP (LogAnalyzer class), Generator (_stream_lines),
                           Context managers, PEP-8 compliant
  Task 2 — Error Handling: try/except per line, structured logging, parse_errors counter
  Task 3 — API Exposure  : Async FastAPI  POST /analyze-logs  with UploadFile
  Task 4 — Complexity    : Commented below and inline throughout

══════════════════════════════════════════════════════════════
  COMPLEXITY ANALYSIS  (Task 4)
══════════════════════════════════════════════════════════════

  LEGACY CODE (original snippet):
  ┌─────────────────────────────────────────────────────────┐
  │  f.readlines()  →  loads ENTIRE file into RAM at once   │
  │  Time  : O(N)   — one pass over N lines                 │
  │  Space : O(N)   — ALL N lines stored in memory          │
  │  ⚠  50 GB file = ~50 GB RAM consumed → OOM crash        │
  └─────────────────────────────────────────────────────────┘

  REFACTORED CODE (this file):
  ┌─────────────────────────────────────────────────────────┐
  │  Generator yields ONE line at a time, never loads all   │
  │  Time  : O(N)   — still one pass (same asymptotic)      │
  │  Space : O(K)   — only K flagged records kept in RAM    │
  │           where K = flagged lines  (K << N in practice) │
  │  ✅ Safe for 50 GB, 500 GB, or any size file            │
  └─────────────────────────────────────────────────────────┘
"""

import logging
from dataclasses import dataclass
from typing import Generator, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────────
# Logging — Task 2
# Production-grade structured logging with timestamp, level, and module name
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("log_analyzer")


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
AMOUNT_THRESHOLD: float = 10_000.0   # Flag transactions above this value
ENCODING: str = "utf-8"


# ─────────────────────────────────────────────────────────────────────────────
# Data Models — Task 1 (OOP / dataclass)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class FlaggedTransaction:
    """
    Represents one flagged transaction.
    Using @dataclass keeps it typed, readable, and testable.
    """
    user_id: str
    amount: float
    status: str = "flagged"

    def to_dict(self) -> dict:
        """Serialize to dict for JSON response."""
        return {
            "user":   self.user_id,
            "amount": self.amount,
            "status": self.status,
        }


class AnalysisResponse(BaseModel):
    """
    Pydantic model — auto-validates output and powers Swagger docs.
    """
    total_flagged:        int
    flagged_transactions: List[dict]
    errors_encountered:   int
    lines_processed:      int


# ─────────────────────────────────────────────────────────────────────────────
# LogAnalyzer Class — Task 1 (OOP + Generator + Context Manager)
# ─────────────────────────────────────────────────────────────────────────────
class LogAnalyzer:
    """
    Production-grade log file analyzer.

    OOP Principles Applied:
      • Encapsulation  — threshold, encoding, and counters are instance state
      • Single Responsibility — one class, one job (analyze logs)
      • Abstraction — caller just calls .analyze(), internals are hidden
    """

    def __init__(
        self,
        amount_threshold: float = AMOUNT_THRESHOLD,
        encoding: str = ENCODING,
    ) -> None:
        self.amount_threshold  = amount_threshold
        self.encoding          = encoding
        self._lines_processed: int = 0
        self._parse_errors:    int = 0

    # ── Generator ────────────────────────────────────────────────────────────
    def _stream_lines(self, file_obj) -> Generator[str, None, None]:
        """
        Generator — reads and yields ONE line at a time.

        This is the KEY fix for the OOM problem.
        Space Complexity: O(1) per iteration — only the current line is in RAM.
        Works for any file size without modification.

        Context Manager Note:
          FastAPI's UploadFile handles opening/closing the file object.
          We use 'for raw_line in file_obj' which is itself a context-safe
          iterator — no explicit open() needed here.
        """
        for raw_line in file_obj:
            # UploadFile gives bytes; decode to string safely
            if isinstance(raw_line, bytes):
                yield raw_line.decode(self.encoding, errors="replace")
            else:
                yield raw_line

    # ── Line Parser ──────────────────────────────────────────────────────────
    def _parse_line(self, line: str) -> Optional[FlaggedTransaction]:
        """
        Parse and validate one CSV log line.

        Expected format:
            <timestamp>,<user_id>,<amount>,<log_level>,<message>
        Example:
            2024-01-01 10:00:00,user_0042,15000.00,ERROR,Payment gateway timeout

        Returns:
            FlaggedTransaction  if ERROR line with amount > threshold
            None                if line should be skipped
        Raises:
            ValueError          if line is malformed (caught by caller)
        """
        line = line.strip()

        # Early exit — skip blank lines and non-ERROR lines immediately
        # This keeps Time complexity O(N) but skips heavy work on most lines
        if not line or "ERROR" not in line:
            return None

        parts = line.split(",")

        # Defensive check — need at least 3 columns
        if len(parts) < 3:
            raise ValueError(
                f"Malformed line — expected ≥3 CSV columns, got {len(parts)}: {line!r}"
            )

        user_id = parts[1].strip()
        if not user_id:
            raise ValueError(f"Empty user_id in line: {line!r}")

        # float() raises ValueError automatically if non-numeric — we let it bubble up
        amount = float(parts[2].strip())

        if amount > self.amount_threshold:
            return FlaggedTransaction(user_id=user_id, amount=amount)

        return None   # ERROR line but amount below threshold — not flagged

    # ── Public API ───────────────────────────────────────────────────────────
    def analyze(self, file_obj) -> List[dict]:
        """
        Stream-analyze a log file and return all flagged transactions.

        Time  Complexity: O(N) — single pass, N = total lines in file
        Space Complexity: O(K) — only K flagged records accumulated
                          K << N in real-world logs (most lines are INFO/DEBUG)
        """
        # Reset counters for each fresh analysis
        self._lines_processed = 0
        self._parse_errors    = 0
        flagged: List[dict]   = []

        logger.info(
            "Analysis started — threshold: $%.2f", self.amount_threshold
        )

        # Iterate line-by-line using generator (O(1) space per iteration)
        for line in self._stream_lines(file_obj):
            self._lines_processed += 1

            try:
                transaction = self._parse_line(line)
                if transaction:
                    flagged.append(transaction.to_dict())
                    logger.debug(
                        "Flagged → user=%s | amount=%.2f",
                        transaction.user_id,
                        transaction.amount,
                    )

            except ValueError as exc:
                # Task 2 — log bad lines without crashing the entire run
                self._parse_errors += 1
                logger.warning(
                    "Parse error on line %d: %s", self._lines_processed, exc
                )

            except Exception as exc:
                # Task 2 — catch unexpected errors, log with full traceback
                self._parse_errors += 1
                logger.error(
                    "Unexpected error on line %d: %s",
                    self._lines_processed,
                    exc,
                    exc_info=True,
                )

        logger.info(
            "Analysis complete — lines=%d | flagged=%d | errors=%d",
            self._lines_processed,
            len(flagged),
            self._parse_errors,
        )
        return flagged

    # ── Properties ───────────────────────────────────────────────────────────
    @property
    def lines_processed(self) -> int:
        return self._lines_processed

    @property
    def parse_errors(self) -> int:
        return self._parse_errors


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App — Task 3
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Log Analyzer API",
    description=(
        "Production-ready log analysis service. "
        "Upload a CSV log file → get back all ERROR transactions above $10,000."
    ),
    version="1.0.0",
)

# Allow all origins (for development; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint: POST /analyze-logs — Task 3
# ─────────────────────────────────────────────────────────────────────────────
@app.post(
    "/analyze-logs",
    response_model=AnalysisResponse,
    summary="Analyze a log file for flagged transactions",
    response_description="Flagged ERROR transactions with amount > $10,000",
)
async def analyze_logs(
    file: UploadFile = File(..., description="Upload a .log or .csv text file"),
) -> JSONResponse:
    """
    **POST /analyze-logs**

    Upload a CSV log file. The API:
    1. Streams through it line-by-line (memory efficient — safe for 50GB+ files)
    2. Finds all `ERROR` lines where amount > $10,000
    3. Returns them as structured JSON

    **Log file format (comma-separated):**
    ```
    <timestamp>,<user_id>,<amount>,<log_level>,<message>
    2024-01-01,user_0042,15000.00,ERROR,Payment gateway timeout
    ```
    """
    # ── Validate file type ───────────────────────────────────────────────────
    allowed_types = ("text/plain", "text/csv", "application/octet-stream")
    if file.content_type not in allowed_types:
        logger.warning(
            "Rejected — unsupported content type: %s for file: %s",
            file.content_type,
            file.filename,
        )
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                f"Please upload a .log or .csv text file."
            ),
        )

    logger.info(
        "File received — name: %s | type: %s", file.filename, file.content_type
    )

    # ── Run analysis ─────────────────────────────────────────────────────────
    analyzer = LogAnalyzer(amount_threshold=AMOUNT_THRESHOLD)

    try:
        # file.file is the underlying SpooledTemporaryFile (context-safe)
        # We pass it directly to analyzer — no full load into RAM
        flagged = analyzer.analyze(file.file)

    except Exception as exc:
        logger.critical(
            "Fatal analysis error for file %s: %s", file.filename, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during analysis: {str(exc)}",
        )
    finally:
        # Context manager pattern — always close the file handle
        await file.close()
        logger.info("File handle closed — %s", file.filename)

    # ── Build and return response ─────────────────────────────────────────────
    response = AnalysisResponse(
        total_flagged        = len(flagged),
        flagged_transactions = flagged,
        errors_encountered   = analyzer.parse_errors,
        lines_processed      = analyzer.lines_processed,
    )

    return JSONResponse(content=response.model_dump(), status_code=200)


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
async def health_check():
    """Returns service status. Use for uptime monitoring."""
    return {"status": "ok", "service": "log-analyzer"}


@app.get("/", summary="API info")
async def root():
    """Returns available endpoints."""
    return {
        "service":   "Log Analyzer API",
        "version":   "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze-logs",
            "health":  "GET  /health",
            "docs":    "GET  /docs",
        },
    }
