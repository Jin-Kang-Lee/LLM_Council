import json

def inject():
    with open("eval/test_data/test_data.json", "r") as f:
        data = json.load(f)
        
    for tc in data:
        gt = tc.get("ground_truth", {})
        if "business_ops" not in gt:
            gt["business_ops"] = {
                "operational_risk_rating": "Medium", # Generic fallback
                "key_business_risks": [
                    {"risk_type": "Market metrics", "keywords": ["margin", "revenue", "sales"]}
                ]
            }
            if tc["test_id"] == "TC-001":
                gt["business_ops"]["operational_risk_rating"] = "Low"
                gt["business_ops"]["key_business_risks"] = [
                    {"risk_type": "Competition", "keywords": ["hyperscalers", "AI Services"]},
                    {"risk_type": "Concentration", "keywords": ["top 10 customers", "18%"]}
                ]
            elif tc["test_id"] == "TC-002":
                gt["business_ops"]["operational_risk_rating"] = "High"
                gt["business_ops"]["key_business_risks"] = [
                    {"risk_type": "Revenue Contraction", "keywords": ["decline of 12%", "fourth consecutive"]},
                    {"risk_type": "Execution Risk", "keywords": ["120 underperforming stores", "$95 million"]}
                ]
            elif tc["test_id"] == "TC-003":
                gt["business_ops"]["operational_risk_rating"] = "Critical"
                gt["business_ops"]["key_business_risks"] = [
                    {"risk_type": "Deceleration", "keywords": ["decelerated from 26%", "saturation"]},
                    {"risk_type": "Take Rate", "keywords": ["compressed by 8", "SMB segment"]}
                ]

    with open("eval/test_data/test_data.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print("Injected business_ops answer key successfully.")

if __name__ == "__main__":
    inject()
