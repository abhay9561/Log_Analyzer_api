"""
Test Suite — Log Analyzer API
==============================
Covers all 4 tasks from the problem statement:
  Task 1 — OOP + Generator + Refactoring
  Task 2 — Error handling (malformed lines, empty file)
  Task 3 — FastAPI endpoint (upload, response schema, status codes)
  Task 4 — Complexity (generator efficiency test with 10,000 lines)

Run with:
    pytest tests/ -v
"""

import io
import sys
import os

# Make sure Python can find the app package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from app.main import app, LogAnalyzer, FlaggedTransaction, AMOUNT_THRESHOLD

# ─────────────────────────────────────────────────────────────────────────────
# Test Client
# ─────────────────────────────────────────────────────────────────────────────
client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Shared Test Data
# ─────────────────────────────────────────────────────────────────────────────
def make_bytes(lines: list) -> bytes:
    """Helper — join lines and encode to bytes (simulates a real file upload)."""
    return "\n".join(lines).encode("utf-8")


# 5 lines: 3 should be flagged, 1 INFO (skipped), 1 ERROR below threshold
VALID_LOG = make_bytes([
    "2024-01-01,user_001,15000.00,ERROR,Payment gateway timeout",   # ✅ flagged
    "2024-01-01,user_002,500.00,INFO,Login successful",             # ❌ not ERROR
    "2024-01-01,user_003,25000.50,ERROR,Duplicate transaction",     # ✅ flagged
    "2024-01-01,user_004,9999.99,ERROR,Below threshold",            # ❌ amount too low
    "2024-01-01,user_005,10001.00,ERROR,Just above threshold",      # ✅ flagged
])

# Lines that should trigger parse errors
MALFORMED_LOG = make_bytes([
    "THIS_LINE_HAS_NO_COMMAS_AT_ALL",                              # ❌ too few columns
    "2024-01-01,user_001,15000.00,ERROR,Valid line",               # ✅ flagged (1 result)
    ",  ,not_a_number,ERROR,Bad amount field",                     # ❌ float() fails
    "",                                                             # ❌ blank line
])

EMPTY_LOG = b""   # No content at all

# High amounts but not ERROR level — should NOT be flagged
NO_ERROR_LOG = make_bytes([
    "2024-01-01,user_001,99999.00,INFO,High amount but INFO level only",
    "2024-01-01,user_002,50000.00,DEBUG,Debug message only",
])


# ─────────────────────────────────────────────────────────────────────────────
# Task 1 + 2 — Unit Tests: LogAnalyzer class
# ─────────────────────────────────────────────────────────────────────────────
class TestLogAnalyzer:

    def test_flags_three_correct_users(self):
        """Task 1 — OOP: analyzer correctly identifies 3 flagged users."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(VALID_LOG))
        assert len(result) == 3
        flagged_users = {r["user"] for r in result}
        assert "user_001" in flagged_users   # 15000 > 10000 ✅
        assert "user_003" in flagged_users   # 25000 > 10000 ✅
        assert "user_005" in flagged_users   # 10001 > 10000 ✅

    def test_does_not_flag_below_threshold(self):
        """Task 1 — Amount 9999.99 must NOT be flagged (threshold is 10000)."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(VALID_LOG))
        flagged_users = {r["user"] for r in result}
        assert "user_004" not in flagged_users

    def test_skips_non_error_log_levels(self):
        """Task 1 — INFO/DEBUG lines must be skipped even with high amounts."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(NO_ERROR_LOG))
        assert result == []

    def test_empty_file_gives_empty_result(self):
        """Task 2 — Empty file should not crash; return empty list."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(EMPTY_LOG))
        assert result == []
        assert analyzer.lines_processed == 0

    def test_malformed_lines_counted_as_errors(self):
        """Task 2 — Bad lines must be logged as errors without crashing."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(MALFORMED_LOG))
        assert len(result) == 1              # only 1 valid flagged line
        assert analyzer.parse_errors >= 1    # at least 1 bad line logged

    def test_custom_threshold_works(self):
        """Task 1 — Threshold is configurable via constructor."""
        analyzer = LogAnalyzer(amount_threshold=20_000)
        result = analyzer.analyze(io.BytesIO(VALID_LOG))
        # Only user_003 (25000.50) exceeds 20000
        assert len(result) == 1
        assert result[0]["user"] == "user_003"

    def test_every_result_has_flagged_status(self):
        """Task 1 — All results must carry status='flagged'."""
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(VALID_LOG))
        for record in result:
            assert record["status"] == "flagged"

    def test_lines_processed_counter_accurate(self):
        """Task 2 — lines_processed property must count every line including blanks."""
        analyzer = LogAnalyzer()
        analyzer.analyze(io.BytesIO(VALID_LOG))
        assert analyzer.lines_processed == 5

    def test_generator_handles_large_file_efficiently(self):
        """
        Task 4 — Complexity test.
        Generator must handle 10,000 lines without memory issues.
        Every 3rd line (index % 3 == 0) is a flagged ERROR.
        """
        lines = []
        for i in range(10_000):
            if i % 3 == 0:
                lines.append(
                    f"2024-01-01,user_{i:06d},15000.00,ERROR,High value transaction"
                )
            elif i % 3 == 1:
                lines.append(
                    f"2024-01-01,user_{i:06d},500.00,INFO,Normal login"
                )
            else:
                lines.append(
                    f"2024-01-01,user_{i:06d},9000.00,ERROR,Below threshold"
                )

        data = "\n".join(lines).encode("utf-8")
        analyzer = LogAnalyzer()
        result = analyzer.analyze(io.BytesIO(data))

        expected_count = sum(1 for i in range(10_000) if i % 3 == 0)
        assert len(result) == expected_count        # correct flagged count
        assert analyzer.lines_processed == 10_000  # all lines visited


# ─────────────────────────────────────────────────────────────────────────────
# Task 1 — Unit Tests: FlaggedTransaction dataclass
# ─────────────────────────────────────────────────────────────────────────────
class TestFlaggedTransaction:

    def test_to_dict_has_correct_keys(self):
        """to_dict() must return user, amount, status."""
        txn = FlaggedTransaction(user_id="u1", amount=15000.0)
        result = txn.to_dict()
        assert result == {"user": "u1", "amount": 15000.0, "status": "flagged"}

    def test_default_status_is_flagged(self):
        """Default status must be 'flagged'."""
        txn = FlaggedTransaction(user_id="u2", amount=20000.0)
        assert txn.status == "flagged"


# ─────────────────────────────────────────────────────────────────────────────
# Task 3 — Integration Tests: FastAPI Endpoint
# ─────────────────────────────────────────────────────────────────────────────
class TestAnalyzeLogsEndpoint:

    def test_valid_upload_returns_200(self):
        """Task 3 — Valid file upload must return HTTP 200."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.log", VALID_LOG, "text/plain")},
        )
        assert response.status_code == 200

    def test_response_has_all_required_fields(self):
        """Task 3 — Response JSON must contain all 4 required fields."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.log", VALID_LOG, "text/plain")},
        )
        data = response.json()
        assert "total_flagged"        in data
        assert "flagged_transactions" in data
        assert "errors_encountered"   in data
        assert "lines_processed"      in data

    def test_correct_flagged_count_returned(self):
        """Task 3 — API must return exactly 3 flagged transactions for VALID_LOG."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.log", VALID_LOG, "text/plain")},
        )
        data = response.json()
        assert data["total_flagged"] == 3
        assert len(data["flagged_transactions"]) == 3

    def test_flagged_transaction_structure(self):
        """Task 3 — Each flagged item must have user, amount, status fields."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.log", VALID_LOG, "text/plain")},
        )
        for txn in response.json()["flagged_transactions"]:
            assert "user"   in txn
            assert "amount" in txn
            assert "status" in txn
            assert txn["status"] == "flagged"

    def test_empty_file_returns_zero_flagged(self):
        """Task 2 + 3 — Empty file must not crash; return total_flagged = 0."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("empty.log", EMPTY_LOG, "text/plain")},
        )
        assert response.status_code == 200
        assert response.json()["total_flagged"] == 0

    def test_missing_file_returns_422(self):
        """Task 3 — Request without file must return 422 Unprocessable Entity."""
        response = client.post("/analyze-logs")
        assert response.status_code == 422

    def test_wrong_file_type_returns_415(self):
        """Task 3 — Non-text file must be rejected with 415 Unsupported Media."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("report.pdf", b"%PDF-1.4 binary", "application/pdf")},
        )
        assert response.status_code == 415

    def test_lines_processed_matches_file_line_count(self):
        """Task 3 — lines_processed in response must equal actual lines in file."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.log", VALID_LOG, "text/plain")},
        )
        assert response.json()["lines_processed"] == 5

    def test_csv_content_type_also_accepted(self):
        """Task 3 — text/csv content type must also be accepted."""
        response = client.post(
            "/analyze-logs",
            files={"file": ("test.csv", VALID_LOG, "text/csv")},
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Task 3 — Other Endpoints
# ─────────────────────────────────────────────────────────────────────────────
class TestHealthEndpoint:

    def test_health_returns_ok(self):
        """GET /health must return status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "log-analyzer"


class TestRootEndpoint:

    def test_root_returns_service_info(self):
        """GET / must return service name and endpoints."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service"   in data
        assert "endpoints" in data
