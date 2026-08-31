"""
ZeptoBrain — FastAPI Backend
All endpoints for the dashboard
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import sys, os, json
from typing import Optional

import pathlib; _PROJ = pathlib.Path(__file__).parent.parent; sys.path.append(str(pathlib.Path(__file__).parent.parent))
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
from ml.demand_forecast import predict_demand
from ml.spoilage_scorer import get_all_spoilage_alerts, calculate_spoilage_risk
from ml.transfer_optimizer import get_transfer_recommendations

app = FastAPI(
    title="ZeptoBrain API",
    description="Dark Store Inventory Intelligence System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data once at startup ─────────────────────────────────────────────────
df_history = None
stores_meta = None

def get_df():
    global df_history
    if df_history is None:
        df_history = pd.read_csv(str(BASE_DIR / "data" / "inventory_history.csv"))
        df_history['date'] = pd.to_datetime(df_history['date'])
    return df_history

def get_stores():
    global stores_meta
    if stores_meta is None:
        with open(str(BASE_DIR / "data" / "stores.json")) as f:
            stores_meta = json.load(f)
    return stores_meta


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "ZeptoBrain API running", "version": "1.0.0"}


@app.get("/api/summary")
def get_summary():
    """Dashboard overview metrics"""
    df = get_df()
    latest = df['date'].max()
    last_7 = df[df['date'] >= latest - pd.Timedelta(days=7)]

    total_waste_inr = last_7['waste_cost'].sum()
    total_revenue = last_7['revenue'].sum()
    stockout_events = len(last_7[last_7['units_sold'] > last_7['stock_ordered']])
    
    alerts = get_all_spoilage_alerts(df, top_n=100)
    critical_count = len(alerts[alerts['risk_level'] == 'critical']) if not alerts.empty else 0
    high_count = len(alerts[alerts['risk_level'] == 'high']) if not alerts.empty else 0

    transfers = get_transfer_recommendations(df)
    transfer_savings = transfers['total_impact_inr'].sum() if not transfers.empty else 0

    return {
        "total_stores": df['store_id'].nunique(),
        "total_skus": df['sku_id'].nunique(),
        "week_waste_inr": round(total_waste_inr, 2),
        "week_revenue_inr": round(total_revenue, 2),
        "waste_pct_of_revenue": round(total_waste_inr / total_revenue * 100, 2) if total_revenue else 0,
        "stockout_events_week": int(stockout_events),
        "spoilage_alerts": {
            "critical": int(critical_count),
            "high": int(high_count),
            "total": int(len(alerts)) if not alerts.empty else 0
        },
        "transfer_recommendations": int(len(transfers)) if not transfers.empty else 0,
        "transfer_potential_savings_inr": round(float(transfer_savings), 2),
        "data_as_of": str(latest.date())
    }


@app.get("/api/stores")
def get_stores_list():
    """All dark store locations"""
    df = get_df()
    stores = get_stores()
    
    store_stats = df.groupby('store_id').agg(
        total_revenue=('revenue','sum'),
        total_waste=('waste_cost','sum'),
        total_orders=('units_sold','sum')
    ).reset_index()
    
    result = []
    for s in stores:
        stats = store_stats[store_stats['store_id'] == s['store_id']]
        result.append({
            **s,
            "total_revenue_inr": round(float(stats['total_revenue'].values[0]), 2) if len(stats) else 0,
            "total_waste_inr": round(float(stats['total_waste'].values[0]), 2) if len(stats) else 0,
        })
    return result


@app.get("/api/forecast")
def get_forecast(
    store_id: str = Query(..., description="Store ID e.g. MUM001"),
    sku_id: str = Query(..., description="SKU ID e.g. SKU-12345"),
    days: int = Query(7, ge=1, le=30)
):
    """7-day demand forecast for a SKU at a store"""
    df = get_df()
    
    # Validate
    if store_id not in df['store_id'].values:
        raise HTTPException(404, f"Store {store_id} not found")
    if sku_id not in df['sku_id'].values:
        raise HTTPException(404, f"SKU {sku_id} not found")
    
    preds = predict_demand(store_id, sku_id, days_ahead=days, df_history=df)
    
    # Get product info
    product_info = df[df['sku_id'] == sku_id].iloc[0]
    
    # Historical for chart (last 14 days)
    latest = df['date'].max()
    hist = df[
        (df['store_id'] == store_id) &
        (df['sku_id'] == sku_id) &
        (df['date'] >= latest - pd.Timedelta(days=14))
    ].sort_values('date')
    
    historical = [
        {"date": str(r['date'].date()), "units_sold": int(r['units_sold']),
         "stock_ordered": int(r['stock_ordered'])}
        for _, r in hist.iterrows()
    ]
    
    return {
        "store_id": store_id,
        "sku_id": sku_id,
        "product_name": product_info['product_name'],
        "category": product_info['category'],
        "mrp": float(product_info['mrp']),
        "is_perishable": bool(product_info['is_perishable']),
        "shelf_life_days": int(product_info['shelf_life_days']),
        "historical": historical,
        "forecast": preds,
        "recommended_order": int(np.mean([p['predicted_units'] for p in preds]) * 1.1) if preds else 0
    }


@app.get("/api/spoilage-alerts")
def get_spoilage_alerts(
    store_id: Optional[str] = None,
    risk_level: Optional[str] = None,
    top_n: int = Query(20, ge=1, le=100)
):
    """Get spoilage alerts, optionally filtered by store or risk level"""
    df = get_df()
    alerts = get_all_spoilage_alerts(df, top_n=100)
    
    if alerts.empty:
        return {"alerts": [], "total": 0, "total_loss_inr": 0}
    
    if store_id:
        alerts = alerts[alerts['store_id'] == store_id]
    if risk_level:
        alerts = alerts[alerts['risk_level'] == risk_level]
    
    alerts = alerts.head(top_n)
    total_loss = alerts['potential_loss_inr'].sum()
    
    return {
        "alerts": alerts.to_dict('records'),
        "total": len(alerts),
        "total_loss_inr": round(float(total_loss), 2)
    }


@app.get("/api/transfers")
def get_transfers(store_id: Optional[str] = None):
    """Inter-store transfer recommendations"""
    df = get_df()
    recs = get_transfer_recommendations(df)
    
    if recs.empty:
        return {"recommendations": [], "total": 0, "total_savings_inr": 0}
    
    if store_id:
        recs = recs[(recs['from_store_id'] == store_id) | (recs['to_store_id'] == store_id)]
    
    return {
        "recommendations": recs.to_dict('records'),
        "total": len(recs),
        "total_savings_inr": round(float(recs['total_impact_inr'].sum()), 2)
    }


@app.get("/api/skus")
def get_skus(
    store_id: Optional[str] = None,
    category: Optional[str] = None,
    perishable_only: bool = False
):
    """List all SKUs with current stats"""
    df = get_df()
    latest = df['date'].max()
    recent = df[df['date'] >= latest - pd.Timedelta(days=7)]
    
    if store_id:
        recent = recent[recent['store_id'] == store_id]
    if category:
        recent = recent[recent['category'] == category]
    if perishable_only:
        recent = recent[recent['is_perishable'] == 1]
    
    skus = recent.groupby(['sku_id','product_name','category','mrp',
                           'is_perishable','shelf_life_days']).agg(
        avg_daily_sold=('units_sold','mean'),
        total_waste_units=('waste_units','sum'),
        total_waste_inr=('waste_cost','sum'),
        avg_stock_ordered=('stock_ordered','mean')
    ).reset_index()
    
    skus['waste_rate_pct'] = (skus['total_waste_units'] / 
                               (skus['avg_daily_sold'] * 7 + 0.1) * 100).round(1)
    
    return skus.sort_values('total_waste_inr', ascending=False).head(50).to_dict('records')


@app.get("/api/roi")
def get_roi():
    """ROI calculator — how much ZeptoBrain saves"""
    df = get_df()
    
    total_waste_before = df['waste_cost'].sum()
    estimated_reduction = 0.30  # 30% reduction (conservative)
    saved = total_waste_before * estimated_reduction
    
    monthly_waste = total_waste_before / 12
    monthly_saved = saved / 12
    
    per_store = saved / df['store_id'].nunique()
    
    return {
        "annual_waste_before_inr": round(total_waste_before, 0),
        "annual_waste_after_inr": round(total_waste_before - saved, 0),
        "annual_savings_inr": round(saved, 0),
        "monthly_savings_inr": round(monthly_saved, 0),
        "savings_per_store_inr": round(per_store, 0),
        "reduction_pct": int(estimated_reduction * 100),
        "stores": int(df['store_id'].nunique()),
        "skus_tracked": int(df['sku_id'].nunique()),
        "data_points": int(len(df))
    }


@app.get("/api/categories")
def get_categories():
    df = get_df()
    return sorted(df['category'].unique().tolist())


@app.get("/api/reorder-alerts")
def get_reorder_alerts(store_id: Optional[str] = None):
    """
    Items running low — need to reorder from vendor soon.
    Based on: current stock vs predicted demand + vendor lead time (assumed 1 day).
    """
    df = get_df()
    latest = df['date'].max()
    recent = df[df['date'] >= latest - pd.Timedelta(days=7)]

    if store_id:
        recent = recent[recent['store_id'] == store_id]

    summary = recent.groupby(['store_id','store_name','sku_id','product_name',
                               'category','mrp','is_perishable','shelf_life_days']).agg(
        avg_daily_sold=('units_sold','mean'),
        avg_ordered=('stock_ordered','mean'),
    ).reset_index()

    # Simulate current stock = ~30% of avg ordered (end of day)
    summary['current_stock'] = (summary['avg_ordered'] * 0.3).astype(int)
    # Days of stock remaining
    summary['days_of_stock'] = (summary['current_stock'] / (summary['avg_daily_sold'] + 0.1)).round(1)

    # Reorder needed if < 2 days of stock left
    reorder = summary[summary['days_of_stock'] < 2].copy()
    reorder['urgency'] = reorder['days_of_stock'].apply(
        lambda d: 'CRITICAL' if d < 0.5 else 'HIGH' if d < 1 else 'MEDIUM'
    )
    reorder['reorder_qty'] = (reorder['avg_daily_sold'] * 3).astype(int)  # 3-day buffer
    reorder['reorder_cost_inr'] = (reorder['reorder_qty'] * reorder['mrp'] * 0.6).round(2)

    reorder = reorder.sort_values('days_of_stock').head(30)

    return {
        "alerts": reorder.to_dict('records'),
        "total": len(reorder),
        "total_reorder_cost_inr": round(float(reorder['reorder_cost_inr'].sum()), 2)
    }


@app.get("/api/waste-trend")
def get_waste_trend(store_id: Optional[str] = None):
    """Daily waste trend for charts"""
    df = get_df()
    if store_id:
        df = df[df['store_id'] == store_id]
    
    trend = df.groupby('date').agg(
        waste_inr=('waste_cost','sum'),
        revenue=('revenue','sum'),
        units_sold=('units_sold','sum')
    ).reset_index()
    
    trend['date'] = trend['date'].dt.strftime('%Y-%m-%d')
    trend = trend.tail(90)  # last 90 days
    
    return trend.to_dict('records')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
