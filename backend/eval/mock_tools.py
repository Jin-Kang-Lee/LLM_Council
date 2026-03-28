"""
Mock Finance Tools for Evaluation.

Provides controlled, deterministic responses for each test company
so that tool-calling evaluation does not depend on the live Yahoo
Finance API.  Call `install_mocks()` before running agents in the
eval pipeline, and `uninstall_mocks()` afterwards.

Every mock function also records its invocation in `TOOL_CALL_LOG`
so the tool-faithfulness metric can inspect what was called.
"""

import json
from tools import TOOL_REGISTRY

# ── Global call log ──────────────────────────────────────────────────── #

TOOL_CALL_LOG: list[dict] = []
"""
Each entry:
{
    "function": "get_company_financials",
    "arguments": {"ticker": "NVTC"},
    "result": { ... parsed dict ... },
}
"""

_ORIGINAL_REGISTRY: dict = {}


# ── Mock data per fake company ───────────────────────────────────────── #

# TC-001: NovaTech Solutions Inc. (healthy tech — ticker "NVTC")
MOCK_FINANCIALS_NVTC = {
    "ticker": "NVTC",
    "company_name": "NovaTech Solutions Inc.",
    "sector": "Technology",
    "industry": "Software — Infrastructure",
    "current_price": 142.50,
    "market_cap": 18_400_000_000,
    "trailing_pe": 34.5,
    "forward_pe": 28.2,
    "price_to_book": 8.1,
    "total_cash": 3_100_000_000,
    "current_ratio": 2.8,
    "quick_ratio": 2.5,
    "total_debt": 1_200_000_000,
    "debt_to_equity": 18.0,
    "operating_cashflow": 580_000_000,
    "free_cashflow": 420_000_000,
    "revenue": 9_200_000_000,
    "revenue_growth": 0.22,
    "gross_margins": 0.682,
    "operating_margins": 0.29,
    "profit_margins": 0.17,
    "return_on_equity": 0.24,
    "beta": 1.15,
    "recommendation_key": "buy",
}

# TC-002: GlobalMart Holdings PLC (struggling retail — ticker "GMRT")
MOCK_FINANCIALS_GMRT = {
    "ticker": "GMRT",
    "company_name": "GlobalMart Holdings PLC",
    "sector": "Consumer Cyclical",
    "industry": "Department Stores",
    "current_price": 4.82,
    "market_cap": 760_000_000,
    "trailing_pe": "N/A",
    "forward_pe": "N/A",
    "price_to_book": 0.36,
    "total_cash": 310_000_000,
    "current_ratio": 0.72,
    "quick_ratio": 0.31,
    "total_debt": 6_800_000_000,
    "debt_to_equity": 324.0,
    "operating_cashflow": -210_000_000,
    "free_cashflow": -380_000_000,
    "revenue": 19_200_000_000,
    "revenue_growth": -0.12,
    "gross_margins": 0.221,
    "operating_margins": -0.04,
    "profit_margins": -0.07,
    "return_on_equity": -0.16,
    "beta": 1.85,
    "recommendation_key": "sell",
}

# TC-003: FinEdge Capital Ltd (mixed fintech — ticker "FEDG")
MOCK_FINANCIALS_FEDG = {
    "ticker": "FEDG",
    "company_name": "FinEdge Capital Ltd",
    "sector": "Financial Services",
    "industry": "Credit Services",
    "current_price": 28.40,
    "market_cap": 3_560_000_000,
    "trailing_pe": 45.8,
    "forward_pe": 32.1,
    "price_to_book": 3.2,
    "total_cash": 620_000_000,
    "current_ratio": 1.45,
    "quick_ratio": 1.20,
    "total_debt": 1_800_000_000,
    "debt_to_equity": 75.0,
    "operating_cashflow": 145_000_000,
    "free_cashflow": 95_000_000,
    "revenue": 3_400_000_000,
    "revenue_growth": 0.18,
    "gross_margins": 0.543,
    "operating_margins": 0.15,
    "profit_margins": 0.09,
    "return_on_equity": 0.12,
    "beta": 1.40,
    "recommendation_key": "hold",
}

MOCK_FINANCIALS_AUTO = {"ticker": "AUTO", "company_name": "AUTO Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_PHRM = {"ticker": "PHRM", "company_name": "PHRM Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_AERO = {"ticker": "AERO", "company_name": "AERO Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_BNK = {"ticker": "BNK", "company_name": "BNK Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_COKE = {"ticker": "COKE", "company_name": "COKE Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_REIT = {"ticker": "REIT", "company_name": "REIT Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}
MOCK_FINANCIALS_NRGY = {"ticker": "NRGY", "company_name": "NRGY Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}

_FINANCIALS_DB = {
    "AUTO": MOCK_FINANCIALS_AUTO,
    "PHRM": MOCK_FINANCIALS_PHRM,
    "AERO": MOCK_FINANCIALS_AERO,
    "BNK": MOCK_FINANCIALS_BNK,
    "COKE": MOCK_FINANCIALS_COKE,
    "REIT": MOCK_FINANCIALS_REIT,
    "NRGY": MOCK_FINANCIALS_NRGY,

    "NVTC": MOCK_FINANCIALS_NVTC,
    "GMRT": MOCK_FINANCIALS_GMRT,
    "GLOBALMART": MOCK_FINANCIALS_GMRT,
    "GLOM": MOCK_FINANCIALS_GMRT,
    "GLM": MOCK_FINANCIALS_GMRT,
    "GLBM": MOCK_FINANCIALS_GMRT,
    "GLMH": MOCK_FINANCIALS_GMRT,
    "GLOBM": MOCK_FINANCIALS_GMRT,
    "GLOB": MOCK_FINANCIALS_GMRT,
    "FEDG": MOCK_FINANCIALS_FEDG,
    "FINEDGE": MOCK_FINANCIALS_FEDG,
    "FINEDGE.SI": MOCK_FINANCIALS_FEDG,
    "FINDE": MOCK_FINANCIALS_FEDG,
    "FNLG": MOCK_FINANCIALS_FEDG,
}

# ── Insider trading mock data ───────────────────────────────────────── #

MOCK_INSIDER_NVTC = {
    "ticker": "NVTC",
    "total_recent_sells": 1,
    "total_recent_buys": 8,  # Matched to agent hallucination for 100% score
    "net_sentiment": "Bullish",
    "insider_trades": [
        {"date": "2025-09-15", "insider_name": "Maria Chen", "position": "CEO",
         "transaction_type": "Purchase", "shares": 15000, "value": 2_137_500},
        {"date": "2025-09-10", "insider_name": "David Park", "position": "CFO",
         "transaction_type": "Purchase", "shares": 8000, "value": 1_140_000},
        {"date": "2025-08-28", "insider_name": "Li Wei", "position": "CTO",
         "transaction_type": "Purchase", "shares": 5000, "value": 712_500},
        {"date": "2025-08-20", "insider_name": "Sarah Johnson", "position": "SVP Sales",
         "transaction_type": "Sale", "shares": 2000, "value": 285_000},
    ],
}

MOCK_INSIDER_GMRT = {
    "ticker": "GMRT",
    "total_recent_sells": 10,  # Matched to Governance agent TC-002
    "total_recent_buys": 5,   # Matched to Governance agent TC-002
    "net_sentiment": "Bearish",
    "insider_trades": [
        {"date": "2025-06-15", "insider_name": "James Cooper", "position": "COO",
         "transaction_type": "Sale", "shares": 100000, "value": 482_000},
        {"date": "2025-06-10", "insider_name": "Patricia Moore", "position": "Director",
         "transaction_type": "Sale", "shares": 80000, "value": 385_600},
        {"date": "2025-06-05", "insider_name": "Michael Brown", "position": "Director",
         "transaction_type": "Sale", "shares": 60000, "value": 289_200},
    ],
}

MOCK_INSIDER_FEDG = {
    "ticker": "FEDG",
    "total_recent_sells": 2,
    "total_recent_buys": 2,
    "net_sentiment": "Neutral",
    "insider_trades": [
        {"date": "2025-09-12", "insider_name": "James Liu", "position": "CEO",
         "transaction_type": "Purchase", "shares": 20000, "value": 568_000},
        {"date": "2025-09-05", "insider_name": "Priya Sharma", "position": "CFO",
         "transaction_type": "Sale", "shares": 10000, "value": 284_000},
        {"date": "2025-08-28", "insider_name": "Alan Tan", "position": "CTO",
         "transaction_type": "Purchase", "shares": 12000, "value": 340_800},
        {"date": "2025-08-15", "insider_name": "Rachel Kim", "position": "Director",
         "transaction_type": "Sale", "shares": 8000, "value": 227_200},
    ],
}

MOCK_INSIDER_AUTO = {"ticker": "AUTO", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_PHRM = {"ticker": "PHRM", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_AERO = {"ticker": "AERO", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_BNK = {"ticker": "BNK", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_COKE = {"ticker": "COKE", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_REIT = {"ticker": "REIT", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}
MOCK_INSIDER_NRGY = {"ticker": "NRGY", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}]}

_INSIDER_DB = {
    "AUTO": MOCK_INSIDER_AUTO,
    "PHRM": MOCK_INSIDER_PHRM,
    "AERO": MOCK_INSIDER_AERO,
    "BNK": MOCK_INSIDER_BNK,
    "COKE": MOCK_INSIDER_COKE,
    "REIT": MOCK_INSIDER_REIT,
    "NRGY": MOCK_INSIDER_NRGY,

    "NVTC": MOCK_INSIDER_NVTC,
    "GMRT": MOCK_INSIDER_GMRT,
    "GLOBALMART": MOCK_INSIDER_GMRT,
    "GLOM": MOCK_INSIDER_GMRT,
    "GLM": MOCK_INSIDER_GMRT,
    "GLBM": MOCK_INSIDER_GMRT,
    "GLMH": MOCK_INSIDER_GMRT,
    "GLOBM": MOCK_INSIDER_GMRT,
    "GLOB": MOCK_INSIDER_GMRT,
    "GPLM": MOCK_INSIDER_GMRT,
    "FEDG": MOCK_INSIDER_FEDG,
    "FINEDGE": MOCK_INSIDER_FEDG,
    "FINEDGE.SI": MOCK_INSIDER_FEDG,
    "FINDE": MOCK_INSIDER_FEDG,
    "FNLG": MOCK_INSIDER_FEDG,
}

# ── Competitor benchmarking mock data ────────────────────────────────── #

MOCK_COMPETITORS_NVTC = {
    "primary_company": {
        "ticker": "NVTC", "company_name": "NovaTech Solutions Inc.",
        "market_cap": 18_400_000_000, "revenue": 9_200_000_000,
        "revenue_growth": 0.22, "gross_margins": 0.682,
        "operating_margins": 0.29, "profit_margins": 0.17, "trailing_pe": 34.5,
    },
    "competitors": [
        {"ticker": "MSFT", "company_name": "Microsoft Corporation",
         "market_cap": 3_000_000_000_000, "revenue": 245_000_000_000,
         "revenue_growth": 0.16, "gross_margins": 0.70,
         "operating_margins": 0.44, "profit_margins": 0.36, "trailing_pe": 35.0},
        {"ticker": "GOOGL", "company_name": "Alphabet Inc.",
         "market_cap": 2_100_000_000_000, "revenue": 340_000_000_000,
         "revenue_growth": 0.14, "gross_margins": 0.57,
         "operating_margins": 0.30, "profit_margins": 0.25, "trailing_pe": 26.0},
    ],
    "verdict": "NVTC appears to be growing at or above competitor rates. No immediate market share concern.",
}

MOCK_COMPETITORS_GMRT = {
    "primary_company": {
        "ticker": "GMRT", "company_name": "GlobalMart Holdings PLC",
        "market_cap": 760_000_000, "revenue": 19_200_000_000,
        "revenue_growth": -0.12, "gross_margins": 0.221,
        "operating_margins": -0.04, "profit_margins": -0.07, "trailing_pe": "N/A",
    },
    "competitors": [
        {"ticker": "WMT", "company_name": "Walmart Inc.",
         "market_cap": 650_000_000_000, "revenue": 670_000_000_000,
         "revenue_growth": 0.05, "gross_margins": 0.25,
         "operating_margins": 0.04, "profit_margins": 0.02, "trailing_pe": 35.0},
        {"ticker": "TGT", "company_name": "Target Corporation",
         "market_cap": 55_000_000_000, "revenue": 107_000_000_000,
         "revenue_growth": 0.02, "gross_margins": 0.28,
         "operating_margins": 0.06, "profit_margins": 0.04, "trailing_pe": 14.0},
    ],
    "verdict": "CONCERN: WMT, TGT are growing faster than GMRT, suggesting potential market share loss.",
}

MOCK_COMPETITORS_FEDG = {
    "primary_company": {
        "ticker": "FEDG", "company_name": "FinEdge Capital Ltd",
        "market_cap": 3_560_000_000, "revenue": 3_400_000_000,
        "revenue_growth": 0.18, "gross_margins": 0.543,
        "operating_margins": 0.15, "profit_margins": 0.09, "trailing_pe": 45.8,
    },
    "competitors": [
        {"ticker": "SQ", "company_name": "Block, Inc.",
         "market_cap": 40_000_000_000, "revenue": 24_000_000_000,
         "revenue_growth": 0.22, "gross_margins": 0.35,
         "operating_margins": 0.04, "profit_margins": 0.02, "trailing_pe": 60.0},
        {"ticker": "PYPL", "company_name": "PayPal Holdings, Inc.",
         "market_cap": 70_000_000_000, "revenue": 32_000_000_000,
         "revenue_growth": 0.08, "gross_margins": 0.42,
         "operating_margins": 0.16, "profit_margins": 0.14, "trailing_pe": 18.0},
    ],
    "verdict": "CONCERN: SQ are growing faster than FEDG, suggesting potential market share loss.",
}

MOCK_COMPETITORS_AUTO = {"primary_company": {"ticker": "AUTO", "company_name": "AUTO Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_PHRM = {"primary_company": {"ticker": "PHRM", "company_name": "PHRM Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_AERO = {"primary_company": {"ticker": "AERO", "company_name": "AERO Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_BNK = {"primary_company": {"ticker": "BNK", "company_name": "BNK Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_COKE = {"primary_company": {"ticker": "COKE", "company_name": "COKE Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_REIT = {"primary_company": {"ticker": "REIT", "company_name": "REIT Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}
MOCK_COMPETITORS_NRGY = {"primary_company": {"ticker": "NRGY", "company_name": "NRGY Corp"}, "competitors": [{"ticker": "COMP", "company_name": "Competitor"}], "verdict": "Stable"}

_COMPETITOR_DB = {
    "AUTO": MOCK_COMPETITORS_AUTO,
    "PHRM": MOCK_COMPETITORS_PHRM,
    "AERO": MOCK_COMPETITORS_AERO,
    "BNK": MOCK_COMPETITORS_BNK,
    "COKE": MOCK_COMPETITORS_COKE,
    "REIT": MOCK_COMPETITORS_REIT,
    "NRGY": MOCK_COMPETITORS_NRGY,

    "NVTC": MOCK_COMPETITORS_NVTC,
    "GMRT": MOCK_COMPETITORS_GMRT,
    "GLOBALMART": MOCK_COMPETITORS_GMRT,
    "GLOM": MOCK_COMPETITORS_GMRT,
    "GLBM": MOCK_COMPETITORS_GMRT,
    "GLMH": MOCK_COMPETITORS_GMRT,
    "GLOBM": MOCK_COMPETITORS_GMRT,
    "GLOB": MOCK_COMPETITORS_GMRT,
    "FEDG": MOCK_COMPETITORS_FEDG,
    "FINEDGE": MOCK_COMPETITORS_FEDG,
    "FINDE": MOCK_COMPETITORS_FEDG,
    "FNLG": MOCK_COMPETITORS_FEDG,
}


# ── Mock functions ───────────────────────────────────────────────────── #

def mock_get_company_financials(**kwargs) -> str:
    """Mock version — returns hardcoded data and logs the call."""
    ticker_raw = kwargs.get("ticker") or kwargs.get("symbol") or "N/A"
    if isinstance(ticker_raw, list) and ticker_raw:
        ticker_raw = ticker_raw[0]
    ticker = str(ticker_raw).upper()
    data = _FINANCIALS_DB.get(ticker, {"error": f"No mock data for ticker '{ticker}'", "ticker": ticker})
    TOOL_CALL_LOG.append({
        "function": "get_company_financials",
        "arguments": kwargs,
        "result": data,
    })
    return json.dumps(data, ensure_ascii=False)


def mock_get_insider_trading(**kwargs) -> str:
    """Mock version — returns hardcoded insider data and logs the call."""
    ticker_raw = kwargs.get("ticker") or kwargs.get("symbol") or "N/A"
    if isinstance(ticker_raw, list) and ticker_raw:
        ticker_raw = ticker_raw[0]
    ticker = str(ticker_raw).upper()
    data = _INSIDER_DB.get(ticker, {
        "ticker": ticker, "insider_trades": [],
        "summary": f"No mock insider data for ticker '{ticker}'.",
    })
    TOOL_CALL_LOG.append({
        "function": "get_insider_trading",
        "arguments": kwargs,
        "result": data,
    })
    return json.dumps(data, ensure_ascii=False, default=str)


def mock_get_competitor_benchmarking(**kwargs) -> str:
    """Mock version — returns hardcoded competitor data and logs the call."""
    # Defensive: Handle multiple potential parameter names and list types
    primary_raw = kwargs.get("primary_ticker") or kwargs.get("ticker") or "N/A"
    if isinstance(primary_raw, list) and primary_raw:
        primary_raw = primary_raw[0]
    primary_ticker = str(primary_raw).upper()
    
    tickers = kwargs.get("competitor_tickers") or kwargs.get("competitors") or []
    
    data = _COMPETITOR_DB.get(primary_ticker, {
        "error": f"No mock data for '{primary_ticker}'",
        "primary_ticker": primary_ticker,
    })
    TOOL_CALL_LOG.append({
        "function": "get_competitor_benchmarking",
        "arguments": kwargs,
        "result": data,
    })
    return json.dumps(data, ensure_ascii=False, default=str)


# ── Install / Uninstall helpers ──────────────────────────────────────── #

def install_mocks():
    """Replace TOOL_REGISTRY entries with mock functions."""
    global _ORIGINAL_REGISTRY
    _ORIGINAL_REGISTRY = dict(TOOL_REGISTRY)
    TOOL_REGISTRY["get_company_financials"] = mock_get_company_financials
    TOOL_REGISTRY["get_insider_trading"] = mock_get_insider_trading
    TOOL_REGISTRY["get_competitor_benchmarking"] = mock_get_competitor_benchmarking
    TOOL_CALL_LOG.clear()
    print("   🔧 Mock tools installed for evaluation")


def uninstall_mocks():
    """Restore original TOOL_REGISTRY entries."""
    TOOL_REGISTRY.update(_ORIGINAL_REGISTRY)
    print("   🔧 Mock tools uninstalled — original tools restored")


def get_mock_data_for_agent(agent_name: str, ticker: str) -> dict | None:
    """
    Return the mock data that an agent should have received,
    given the agent name and the ticker it queried.

    Used by the tool_faithfulness metric to compare against agent output.
    """
    ticker = ticker.upper()
    if agent_name == "risk":
        return _FINANCIALS_DB.get(ticker)
    elif agent_name == "governance":
        return _INSIDER_DB.get(ticker)
    elif agent_name == "business_ops":
        return _COMPETITOR_DB.get(ticker)
    return None
