"""
Finance Tools — yfinance wrapper for agent tool calling.

Provides structured financial data that agents can request via Ollama's
tool-calling (function-calling) interface.
"""

import json
import yfinance as yf


def get_company_financials(ticker: str) -> str:
    """
    Fetch key financial metrics for a given stock ticker using yfinance.

    Returns a focused JSON string containing the metrics most relevant
    to the Financial Risk Agent's analysis mandate (liquidity, leverage,
    cash flow, valuation).

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "DBS.SI", "MSFT")

    Returns:
        JSON string with financial metrics, or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Guard against invalid tickers — yfinance returns an almost-empty
        # dict when the ticker doesn't exist.
        if not info or info.get("regularMarketPrice") is None:
            return json.dumps({
                "error": f"No data found for ticker '{ticker}'. "
                         "Please verify the ticker symbol is correct.",
                "ticker": ticker,
            })

        def safe_get(key, default="N/A"):
            """Return the value or a safe default."""
            val = info.get(key)
            return val if val is not None else default

        metrics = {
            "ticker": ticker.upper(),
            "company_name": safe_get("longName"),
            "sector": safe_get("sector"),
            "industry": safe_get("industry"),

            # --- Price & Valuation ---
            "current_price": safe_get("regularMarketPrice"),
            "market_cap": safe_get("marketCap"),
            "trailing_pe": safe_get("trailingPE"),
            "forward_pe": safe_get("forwardPE"),
            "price_to_book": safe_get("priceToBook"),

            # --- Liquidity & Working Capital ---
            "total_cash": safe_get("totalCash"),
            "current_ratio": safe_get("currentRatio"),
            "quick_ratio": safe_get("quickRatio"),

            # --- Leverage / Debt ---
            "total_debt": safe_get("totalDebt"),
            "debt_to_equity": safe_get("debtToEquity"),

            # --- Cash Flow ---
            "operating_cashflow": safe_get("operatingCashflow"),
            "free_cashflow": safe_get("freeCashflow"),

            # --- Profitability ---
            "revenue": safe_get("totalRevenue"),
            "revenue_growth": safe_get("revenueGrowth"),
            "gross_margins": safe_get("grossMargins"),
            "operating_margins": safe_get("operatingMargins"),
            "profit_margins": safe_get("profitMargins"),
            "return_on_equity": safe_get("returnOnEquity"),

            # --- Risk Indicators ---
            "beta": safe_get("beta"),
            "recommendation_key": safe_get("recommendationKey"),
        }

        return json.dumps(metrics, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch financials for '{ticker}': {str(e)}",
            "ticker": ticker,
        })


def get_insider_trading(ticker: str) -> str:
    """
    Fetch recent insider trading (SEC Form 4) data for a given stock ticker.

    Returns a JSON string summarising recent insider buy/sell transactions
    by executives and board members.  This is used by the Governance Agent
    to detect whether management's public statements align with their
    personal trading behaviour.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "DBS.SI", "MSFT")

    Returns:
        JSON string with insider transactions, or an error message.
    """
    try:
        stock = yf.Ticker(ticker)
        transactions = stock.insider_transactions

        # yfinance returns a DataFrame; guard against empty / None
        if transactions is None or (hasattr(transactions, "empty") and transactions.empty):
            return json.dumps({
                "ticker": ticker.upper(),
                "insider_trades": [],
                "summary": "No insider trading data available for this ticker.",
            })

        # Convert DataFrame to list of dicts, keep only the most recent 15
        records = transactions.head(15).to_dict(orient="records")

        # Clean up each record for the LLM
        cleaned = []
        for row in records:
            cleaned.append({
                "date": str(row.get("Date", row.get("Start Date", "N/A"))),
                "insider_name": str(row.get("Insider", row.get("Name", "N/A"))),
                "position": str(row.get("Position", row.get("Title", "N/A"))),
                "transaction_type": str(row.get("Transaction", row.get("Text", "N/A"))),
                "shares": row.get("Shares", row.get("#Shares", "N/A")),
                "value": row.get("Value", "N/A"),
            })

        # Quick summary stats
        total_sells = sum(1 for t in cleaned if "sale" in str(t["transaction_type"]).lower()
                         or "sell" in str(t["transaction_type"]).lower())
        total_buys = sum(1 for t in cleaned if "purchase" in str(t["transaction_type"]).lower()
                        or "buy" in str(t["transaction_type"]).lower())

        result = {
            "ticker": ticker.upper(),
            "total_recent_sells": total_sells,
            "total_recent_buys": total_buys,
            "net_sentiment": "Bearish" if total_sells > total_buys else (
                "Bullish" if total_buys > total_sells else "Neutral"
            ),
            "insider_trades": cleaned,
        }

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch insider trading for '{ticker}': {str(e)}",
            "ticker": ticker,
        })


def get_competitor_benchmarking(primary_ticker: str, competitor_tickers: list[str] = None, **kwargs) -> str:
    """
    Compare a company's key performance metrics against its competitors.

    Pulls revenue growth, gross margins, operating margins, and market cap
    for the primary company and up to 3 competitors, returning a side-by-side
    comparison grid.

    Args:
        primary_ticker: Ticker of the company being analyzed (e.g. "AAPL")
        competitor_tickers: List of up to 3 competitor tickers (e.g. ["MSFT", "GOOGL"])

    Returns:
        JSON string with a comparison grid, or an error message.
    """
    # Defensive: Handle cases where model might pass 'competitors' instead of 'competitor_tickers'
    tickers = competitor_tickers or kwargs.get("competitors") or []
    
    def _fetch_metrics(ticker: str) -> dict:
        """Pull the comparison-relevant metrics for a single ticker."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info or info.get("regularMarketPrice") is None:
                return {"ticker": ticker.upper(), "error": "No data found"}

            def safe_get(key, default="N/A"):
                val = info.get(key)
                return val if val is not None else default

            return {
                "ticker": ticker.upper(),
                "company_name": safe_get("longName"),
                "market_cap": safe_get("marketCap"),
                "revenue": safe_get("totalRevenue"),
                "revenue_growth": safe_get("revenueGrowth"),
                "gross_margins": safe_get("grossMargins"),
                "operating_margins": safe_get("operatingMargins"),
                "profit_margins": safe_get("profitMargins"),
                "trailing_pe": safe_get("trailingPE"),
            }
        except Exception as e:
            return {"ticker": ticker.upper(), "error": str(e)}

    try:
        # Cap competitors at 3 to avoid excessive API calls
        competitors = tickers[:3]

        primary = _fetch_metrics(primary_ticker)
        competitor_data = [_fetch_metrics(t) for t in competitors]

        # Build a quick verdict
        primary_growth = primary.get("revenue_growth")
        faster_rivals = []
        for comp in competitor_data:
            comp_growth = comp.get("revenue_growth")
            if (isinstance(primary_growth, (int, float))
                    and isinstance(comp_growth, (int, float))
                    and comp_growth > primary_growth):
                faster_rivals.append(comp.get("ticker", "?"))

        if faster_rivals:
            verdict = (f"CONCERN: {', '.join(faster_rivals)} are growing faster "
                       f"than {primary_ticker.upper()}, suggesting potential market share loss.")
        else:
            verdict = (f"{primary_ticker.upper()} appears to be growing at or above "
                       f"competitor rates. No immediate market share concern.")

        result = {
            "primary_company": primary,
            "competitors": competitor_data,
            "verdict": verdict,
        }

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to run competitor benchmarking: {str(e)}",
            "primary_ticker": primary_ticker,
        })


# --------------------------------------------------------------------- #
#  Ollama / OpenAI-compatible tool definition
# --------------------------------------------------------------------- #

FINANCE_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_company_financials",
        "description": (
            "Fetch real-time financial metrics for a publicly-traded company "
            "using its stock ticker symbol. Returns liquidity ratios, leverage "
            "metrics, cash flow data, profitability margins, and valuation "
            "multiples. Use this to fact-check claims made in the earnings "
            "report against actual market data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol of the company to look up. "
                        "Examples: 'AAPL' for Apple, 'DBS.SI' for DBS Group, "
                        "'MSFT' for Microsoft."
                    ),
                },
            },
            "required": ["ticker"],
        },
    },
}

INSIDER_TRADING_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_insider_trading",
        "description": (
            "Fetch recent insider trading (SEC Form 4) data for a publicly-traded "
            "company. Returns a list of recent buy and sell transactions made by "
            "executives, directors, and board members. Use this to check whether "
            "management's public optimism aligns with their personal stock trades."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol of the company to look up. "
                        "Examples: 'AAPL' for Apple, 'DBS.SI' for DBS Group, "
                        "'MSFT' for Microsoft."
                    ),
                },
            },
            "required": ["ticker"],
        },
    },
}

COMPETITOR_BENCHMARKING_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_competitor_benchmarking",
        "description": (
            "Compare a company's financial performance against its competitors. "
            "Takes the primary company's ticker and a list of competitor tickers, "
            "then returns a side-by-side comparison of revenue growth, gross margins, "
            "operating margins, and market cap. Use this to assess whether the company "
            "is gaining or losing market share relative to its industry peers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "primary_ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker of the company being analyzed. "
                        "Example: 'AAPL' for Apple."
                    ),
                },
                "competitor_tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "A list of up to 3 competitor stock tickers. "
                        "Example: ['MSFT', 'GOOGL', 'AMZN']"
                    ),
                },
            },
            "required": ["primary_ticker", "competitor_tickers"],
        },
    },
}


# --------------------------------------------------------------------- #
#  Registries — used by BaseAgent to dispatch tool calls at runtime
# --------------------------------------------------------------------- #

# Maps function name → callable
TOOL_REGISTRY: dict[str, callable] = {
    "get_company_financials": get_company_financials,
    "get_insider_trading": get_insider_trading,
    "get_competitor_benchmarking": get_competitor_benchmarking,
}

# List of tool definitions to pass to Ollama /api/chat
TOOL_DEFINITIONS: list[dict] = [
    FINANCE_TOOL_DEFINITION,
    INSIDER_TRADING_TOOL_DEFINITION,
    COMPETITOR_BENCHMARKING_TOOL_DEFINITION,
]
