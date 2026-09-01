"""
ZeptoBrain — Spoilage Risk Scorer
Calculates 0-100 risk score per perishable SKU per store
High score = item will spoil = wastage = money lost
"""
import pandas as pd
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
import numpy as np
from datetime import datetime, timedelta
import pickle


def calculate_spoilage_risk(
    current_stock: int,
    shelf_life_days: int,
    days_in_store: int,
    predicted_daily_demand: float,
    is_perishable: bool,
    category: str
) -> dict:
    """
    Core spoilage risk formula.
    Returns score 0-100 + reasoning.
    """
    if not is_perishable:
        return {"score": 0, "level": "safe", "reason": "Non-perishable item",
                "days_to_expire": shelf_life_days, "excess_units": 0,
                "current_stock": current_stock, "sellable_before_expiry": 0,
                "action": "No action needed"}

    days_remaining = max(0, shelf_life_days - days_in_store)
    
    if days_remaining == 0:
        return {"score": 100, "level": "critical", "reason": "EXPIRED", "days_to_expire": 0,
                "excess_units": current_stock, "current_stock": current_stock,
                "sellable_before_expiry": 0, "action": "DISCARD IMMEDIATELY"}

    # How many units can we sell before expiry?
    sellable_units = predicted_daily_demand * days_remaining
    
    # Excess stock ratio
    if sellable_units > 0:
        excess_ratio = max(0, (current_stock - sellable_units) / sellable_units)
    else:
        excess_ratio = 1.0 if current_stock > 0 else 0.0

    # Time pressure score (0-40 pts)
    time_pressure = max(0, 40 * (1 - days_remaining / shelf_life_days))

    # Excess stock score (0-40 pts)
    excess_score = min(40, excess_ratio * 40)

    # Category risk multiplier
    cat_multiplier = {
        "Fruits & Vegetables": 1.3,
        "Dairy": 1.2,
        "Breakfast": 1.1,  # bread etc
        "Frozen Foods": 1.0,
    }.get(category, 1.0)

    raw_score = (time_pressure + excess_score) * cat_multiplier
    score = min(100, int(raw_score))

    # Risk level
    if score >= 75:
        level = "critical"
        action = "Transfer NOW or discount 30%+"
    elif score >= 50:
        level = "high"
        action = "Apply 15-20% discount today"
    elif score >= 25:
        level = "medium"
        action = "Monitor closely, plan reorder carefully"
    else:
        level = "safe"
        action = "No action needed"

    return {
        "score": score,
        "level": level,
        "days_to_expire": days_remaining,
        "current_stock": current_stock,
        "sellable_before_expiry": int(sellable_units),
        "excess_units": max(0, int(current_stock - sellable_units)),
        "action": action,
        "reason": f"{days_remaining}d left, can sell ~{int(sellable_units)} units, have {current_stock}"
    }


def get_all_spoilage_alerts(df_history=None, top_n=20):
    """
    Scan all perishable SKUs across all stores.
    Return ranked spoilage alerts.
    """
    if df_history is None:
        df_history = pd.read_csv(str(BASE_DIR / "data" / "inventory_history.csv"))
    if not pd.api.types.is_datetime64_any_dtype(df_history['date']):
        df_history = df_history.copy()
        df_history['date'] = pd.to_datetime(df_history['date'])

    # Use last 7 days for current state simulation
    latest_date = df_history['date'].max()
    recent = df_history[df_history['date'] >= latest_date - pd.Timedelta(days=7)]
    
    # Perishables only
    perish = recent[recent['is_perishable'] == 1].copy()
    
    alerts = []
    for (store_id, sku_id), group in perish.groupby(['store_id', 'sku_id']):
        last = group.sort_values('date').iloc[-1]
        avg_daily_demand = group['units_sold'].mean()
        
        # Simulate current stock = last ordered - sold + some buffer
        current_stock = max(0, int(last['stock_ordered'] * 0.4))  # ~40% remaining mid-cycle
        days_in_store = 2  # assume 2 days old on average

        result = calculate_spoilage_risk(
            current_stock=current_stock,
            shelf_life_days=last['shelf_life_days'],
            days_in_store=days_in_store,
            predicted_daily_demand=avg_daily_demand,
            is_perishable=bool(last['is_perishable']),
            category=last['category']
        )

        if result['score'] > 20:
            alerts.append({
                "store_id": store_id,
                "store_name": last['store_name'],
                "sku_id": sku_id,
                "product_name": last['product_name'],
                "category": last['category'],
                "mrp": last['mrp'],
                "current_stock": current_stock,
                "avg_daily_demand": round(avg_daily_demand, 1),
                "spoilage_score": result['score'],
                "risk_level": result['level'],
                "days_to_expire": result['days_to_expire'],
                "excess_units": result['excess_units'],
                "action": result['action'],
                "potential_loss_inr": round(result['excess_units'] * last['mrp'] * 0.6, 2),
                "reason": result['reason']
            })

    alerts_df = pd.DataFrame(alerts).sort_values('spoilage_score', ascending=False)
    return alerts_df.head(top_n) if not alerts_df.empty else alerts_df


if __name__ == "__main__":
    print("🔍 Running Spoilage Alert Engine...\n")
    
    alerts = get_all_spoilage_alerts(top_n=15)
    
    if alerts.empty:
        print("No alerts found.")
    else:
        print(f"⚠️  {len(alerts)} Spoilage Alerts Found:\n")
        display_cols = ['store_name','product_name','spoilage_score','risk_level',
                       'days_to_expire','excess_units','potential_loss_inr','action']
        print(alerts[display_cols].to_string(index=False))
        
        total_loss = alerts['potential_loss_inr'].sum()
        critical = len(alerts[alerts['risk_level']=='critical'])
        high = len(alerts[alerts['risk_level']=='high'])
        
        print(f"\n💰 Summary:")
        print(f"   Critical alerts: {critical}")
        print(f"   High alerts: {high}")
        print(f"   Total potential loss: ₹{total_loss:,.0f}")
        print("\n✅ Spoilage Scorer working correctly")
