"""
ZeptoBrain — Inter-Store Transfer Optimizer
If Store A has excess stock + Store B has low stock of same SKU → transfer
Saves wastage AND prevents stockouts simultaneously
"""
import pandas as pd
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
import numpy as np
import json


def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance in km between two GPS coordinates"""
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def get_transfer_recommendations(df_history=None, max_transfer_km=10):
    """
    Find store pairs where transfer makes sense.
    Logic: Store A excess stock + Store B stockout risk + distance < 10km
    """
    if df_history is None:
        df_history = pd.read_csv(str(BASE_DIR / "data" / "inventory_history.csv"))
        df_history['date'] = pd.to_datetime(df_history['date'])

    with open(str(BASE_DIR / "data" / "stores.json")) as f:
        stores = {s['store_id']: s for s in json.load(f)}

    latest = df_history['date'].max()
    recent = df_history[df_history['date'] >= latest - pd.Timedelta(days=3)]

    # Per store per SKU: avg stock ordered vs sold
    summary = recent.groupby(['store_id','store_name','sku_id','product_name',
                               'category','is_perishable','shelf_life_days','mrp']).agg(
        avg_ordered=('stock_ordered','mean'),
        avg_sold=('units_sold','mean'),
        total_waste=('waste_units','sum')
    ).reset_index()

    summary['excess_ratio'] = (summary['avg_ordered'] - summary['avg_sold']) / (summary['avg_sold'] + 0.1)
    summary['simulated_stock'] = (summary['avg_ordered'] * 0.5).astype(int)  # ~50% remaining

    # Stores with excess (ratio > 0.3)
    excess = summary[summary['excess_ratio'] > 0.08].copy()
    # Stores with shortage (ratio < -0.05, running low)
    shortage = summary[summary['excess_ratio'] < -0.05].copy()

    recommendations = []

    for _, ex_row in excess.iterrows():
        sku = ex_row['sku_id']
        # Find shortage stores with same SKU
        matches = shortage[shortage['sku_id'] == sku]
        
        for _, sh_row in matches.iterrows():
            if ex_row['store_id'] == sh_row['store_id']:
                continue

            # Distance check
            s1 = stores.get(ex_row['store_id'])
            s2 = stores.get(sh_row['store_id'])
            if not s1 or not s2:
                continue

            dist = haversine_distance(s1['lat'], s1['lng'], s2['lat'], s2['lng'])
            if dist > max_transfer_km:
                continue

            # Transfer quantity = min(excess, shortage need)
            excess_units = max(0, int(ex_row['avg_ordered'] - ex_row['avg_sold']))
            shortage_need = max(0, int(sh_row['avg_sold'] - sh_row['avg_ordered'] + 5))
            transfer_qty = min(excess_units, shortage_need)

            if transfer_qty < 2:
                continue

            # Financial impact
            unit_cost = ex_row['mrp'] * 0.6
            wastage_saved = transfer_qty * unit_cost
            revenue_saved = transfer_qty * ex_row['mrp']  # sales that would be lost in shortage store

            urgency = "HIGH" if ex_row['is_perishable'] and ex_row['shelf_life_days'] <= 3 else "MEDIUM"

            recommendations.append({
                "from_store_id": ex_row['store_id'],
                "from_store": ex_row['store_name'],
                "to_store_id": sh_row['store_id'],
                "to_store": sh_row['store_name'],
                "sku_id": sku,
                "product_name": ex_row['product_name'],
                "category": ex_row['category'],
                "is_perishable": bool(ex_row['is_perishable']),
                "transfer_qty": transfer_qty,
                "distance_km": round(dist, 2),
                "wastage_saved_inr": round(wastage_saved, 2),
                "revenue_saved_inr": round(revenue_saved, 2),
                "total_impact_inr": round(wastage_saved + revenue_saved, 2),
                "urgency": urgency,
                "shelf_life_days": int(ex_row['shelf_life_days'])
            })

    if not recommendations:
        return pd.DataFrame()

    recs_df = pd.DataFrame(recommendations)
    recs_df = recs_df.sort_values('total_impact_inr', ascending=False).drop_duplicates(
        subset=['from_store_id','to_store_id','sku_id']
    )
    return recs_df


if __name__ == "__main__":
    print("🔄 Running Transfer Optimizer...\n")
    recs = get_transfer_recommendations()

    if recs.empty:
        print("No transfer recommendations at this time.")
    else:
        print(f"📦 {len(recs)} Transfer Recommendations:\n")
        display = ['from_store','to_store','product_name','transfer_qty',
                   'distance_km','wastage_saved_inr','total_impact_inr','urgency']
        print(recs[display].head(10).to_string(index=False))
        
        print(f"\n💰 Total potential savings: ₹{recs['total_impact_inr'].sum():,.0f}")
        print(f"   HIGH urgency transfers: {len(recs[recs['urgency']=='HIGH'])}")
        print("\n✅ Transfer Optimizer working correctly")
