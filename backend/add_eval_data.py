import json
import os
import sys

TEST_DATA_PATH = r"c:\Users\jinka\OneDrive\Documents\GitHub\LLM_Council\backend\eval\test_data\test_data.json"
MOCK_TOOLS_PATH = r"c:\Users\jinka\OneDrive\Documents\GitHub\LLM_Council\backend\eval\mock_tools.py"

NEW_CASES = [
    {
        "test_id": "TC-004",
        "description": "Legacy automaker transitioning to EV",
        "earnings_report": "AUTO MOTORS INC.\nQuarterly Earnings Report — Q3 FY2025\n\nFINANCIAL HIGHLIGHTS\nRevenue dropped 5% YoY to $32.4 billion. EV segment grew 40% but margins are negative. Legacy ICE segment margins compressed to 8%. We issued $4B in new debt to fund battery plants.\n\nGUIDANCE\nFull year guidance lowered due to weak China sales.\n\nRISK FACTORS\nHigh debt, supply chain delays for lithium, intense EV competition.\n\nGOVERNANCE\nCEO recently sold 50,000 shares. No major litigation.",
        "ground_truth": {
            "risk": {
                "overall_risk_rating": "High",
                "tool_eval": {"expected_ticker": "AUTO", "expected_tool": "get_company_financials"}
            },
            "business_ops": {
                "tool_eval": {"expected_ticker": "AUTO", "expected_tool": "get_competitor_benchmarking"}
            },
            "governance": {
                "tool_eval": {"expected_ticker": "AUTO", "expected_tool": "get_insider_trading"}
            },
            "rag": {"risk": {"expected_sources": ["Damodaran_Debt_Sector_Fundamentals.md"], "expected_keywords": ["debt", "margin"]}}
        }
    },
    {
        "test_id": "TC-005",
        "description": "Biotech facing patent cliff",
        "earnings_report": "NEXTGEN PHARMA\nQ3 FY2025\n\nRevenue grew 10% to $5.2B. Our leading drug faces patent expiration next year. Pipeline is strong but delayed by FDA scrutiny.\n\nRISK\nPatent cliff, FDA delays.\nGOVERNANCE\nClean audit, CFO bought 10k shares.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "PHRM", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "PHRM", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "PHRM", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    },
    {
        "test_id": "TC-006",
        "description": "Aerospace with supply chain woes",
        "earnings_report": "AEROSKY DYNAMICS\nQ2 FY2025\n\nRevenue flat at $12B. Deliveries halted due to fuselage defects. $500M penalty paid. Margins took a hit.\n\nRISK\nQuality control, supply chain.\nGOVERNANCE\nGovernment probe ongoing.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "AERO", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "AERO", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "AERO", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    },
    {
        "test_id": "TC-007",
        "description": "Regional Bank with CRE exposure",
        "earnings_report": "HEARTLAND BANK\nQ1 FY2025\n\nNet interest margin compressed to 2.4%. Commercial Real Estate (CRE) loan defaults rose 1.5%. Provision for credit losses increased by 200%. Deposits stabilized after Q4 outflows.\n\nRISK\nCRE exposure, NIM compression.\nGOVERNANCE\nAudit committee met 8 times.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "BNK", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "BNK", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "BNK", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    },
    {
        "test_id": "TC-008",
        "description": "Beverage giant with steady growth",
        "earnings_report": "GLOBAL COLA CORP\nQ4 FY2025\n\nOrganic revenue grew 5%, driven by pricing power. Volumes flat. Operating margin expanded to 31%. Strong free cash flow of $8B.\n\nRISK\nFX headwinds, ingredient inflation.\nGOVERNANCE\nStandard, clean disclosures.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "COKE", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "COKE", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "COKE", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    },
    {
        "test_id": "TC-009",
        "description": "Office REIT struggling with vacancies",
        "earnings_report": "METRO PROPERTIES REIT\nQ3 FY2025\n\nFunds From Operations (FFO) dropped 18%. Office occupancy sits at 76%. Exploring conversion of 3 properties to residential. Debt refinancing coming up next year at higher rates.\n\nRISK\nRefinancing at high rates, vacancy.\nGOVERNANCE\nDividend cut by 40%.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "REIT", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "REIT", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "REIT", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    },
    {
        "test_id": "TC-010",
        "description": "Renewable energy firm hit by rates",
        "earnings_report": "SUNWIND ENERGY\nQ2 FY2025\n\nProjects delayed due to financing costs. Revenue up 12% but net loss widened. Backlog stands at $4B. \n\nRISK\nInterest rates pricing out projects.\nGOVERNANCE\nCFO resigned.",
        "ground_truth": {
            "risk": {"tool_eval": {"expected_ticker": "NRGY", "expected_tool": "get_company_financials"}},
            "business_ops": {"tool_eval": {"expected_ticker": "NRGY", "expected_tool": "get_competitor_benchmarking"}},
            "governance": {"tool_eval": {"expected_ticker": "NRGY", "expected_tool": "get_insider_trading"}},
            "rag": {}
        }
    }
]

import hashlib

def get_db_lines():
    mock_financials = ""
    mock_insiders = ""
    mock_competitors = ""
    db_financials = ""
    db_insiders = ""
    db_competitors = ""
    
    for tc in NEW_CASES:
        t = tc["ground_truth"]["risk"]["tool_eval"]["expected_ticker"]
        mock_financials += f'''MOCK_FINANCIALS_{t} = {{"ticker": "{t}", "company_name": "{t} Corp", "sector": "Various", "industry": "Various", "current_price": 50.0, "market_cap": 10000000000, "trailing_pe": 20, "forward_pe": 18, "price_to_book": 2.5, "total_cash": 1000000000, "current_ratio": 1.5, "quick_ratio": 1.2, "total_debt": 2000000000, "debt_to_equity": 50.0, "operating_cashflow": 500000000, "free_cashflow": 300000000, "revenue": 5000000000, "revenue_growth": 0.1, "gross_margins": 0.4, "operating_margins": 0.15, "profit_margins": 0.1, "return_on_equity": 0.15, "beta": 1.0, "recommendation_key": "hold"}}\n'''
        db_financials += f'    "{t}": MOCK_FINANCIALS_{t},\n'
        
        mock_insiders += f'''MOCK_INSIDER_{t} = {{"ticker": "{t}", "total_recent_sells": 1, "total_recent_buys": 1, "net_sentiment": "Neutral", "insider_trades": [{{"date": "2025-01-01", "insider_name": "John Doe", "position": "CEO", "transaction_type": "Purchase", "shares": 1000, "value": 50000}}]}}\n'''
        db_insiders += f'    "{t}": MOCK_INSIDER_{t},\n'
        
        mock_competitors += f'''MOCK_COMPETITORS_{t} = {{"primary_company": {{"ticker": "{t}", "company_name": "{t} Corp"}}, "competitors": [{{"ticker": "COMP", "company_name": "Competitor"}}], "verdict": "Stable"}}\n'''
        db_competitors += f'    "{t}": MOCK_COMPETITORS_{t},\n'
        
    return mock_financials, db_financials, mock_insiders, db_insiders, mock_competitors, db_competitors

try:
    with open(TEST_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    existing_ids = {item["test_id"] for item in data}
    for item in NEW_CASES:
        if item["test_id"] not in existing_ids:
            data.append(item)
            
    with open(TEST_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    with open(MOCK_TOOLS_PATH, "r", encoding="utf-8") as f:
        mock_content = f.read()

    mf, df, mi, di, mc, dc = get_db_lines()
    
    if "MOCK_FINANCIALS_AUTO" not in mock_content:
        mock_content = mock_content.replace("_FINANCIALS_DB = {", mf + "\n_FINANCIALS_DB = {\n" + df)
        mock_content = mock_content.replace("_INSIDER_DB = {", mi + "\n_INSIDER_DB = {\n" + di)
        mock_content = mock_content.replace("_COMPETITOR_DB = {", mc + "\n_COMPETITOR_DB = {\n" + dc)
        
        with open(MOCK_TOOLS_PATH, "w", encoding="utf-8") as f:
            f.write(mock_content)
    
    print("Successfully added 7 test cases and mock data!")
except Exception as e:
    print(f"Error: {e}")
