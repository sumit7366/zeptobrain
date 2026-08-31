"""
ZeptoBrain Data Generator
Generates realistic dark store inventory data mimicking Zepto's actual catalog
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

from pathlib import Path
BASE_DIR = Path(__file__).parent.parent

np.random.seed(42)
random.seed(42)

# ── Real Zepto-style product catalog ─────────────────────────────────────────
PRODUCTS = [
    # (name, category, mrp, shelf_life_days, is_perishable)
    # Fruits & Vegetables
    ("Tomatoes 1kg", "Fruits & Vegetables", 45, 4, True),
    ("Onions 1kg", "Fruits & Vegetables", 35, 14, True),
    ("Potatoes 1kg", "Fruits & Vegetables", 30, 20, True),
    ("Spinach 250g", "Fruits & Vegetables", 20, 2, True),
    ("Capsicum 500g", "Fruits & Vegetables", 55, 5, True),
    ("Carrots 500g", "Fruits & Vegetables", 35, 7, True),
    ("Cucumber 500g", "Fruits & Vegetables", 25, 4, True),
    ("Lemon 6pcs", "Fruits & Vegetables", 30, 7, True),
    ("Coriander 100g", "Fruits & Vegetables", 15, 2, True),
    ("Ginger 100g", "Fruits & Vegetables", 20, 10, True),
    ("Garlic 100g", "Fruits & Vegetables", 35, 15, True),
    ("Banana 6pcs", "Fruits & Vegetables", 40, 3, True),
    ("Apple Royal 4pcs", "Fruits & Vegetables", 120, 7, True),
    ("Grapes 500g", "Fruits & Vegetables", 90, 4, True),
    ("Mango Alphonso 500g", "Fruits & Vegetables", 150, 3, True),
    ("Watermelon 1pc", "Fruits & Vegetables", 80, 5, True),
    ("Peas 500g", "Fruits & Vegetables", 45, 3, True),
    ("Broccoli 500g", "Fruits & Vegetables", 60, 3, True),
    ("Mushroom 200g", "Fruits & Vegetables", 55, 3, True),
    ("Bitter Gourd 500g", "Fruits & Vegetables", 35, 5, True),
    # Dairy
    ("Amul Milk 1L", "Dairy", 68, 3, True),
    ("Amul Butter 500g", "Dairy", 280, 90, False),
    ("Mother Dairy Curd 400g", "Dairy", 45, 5, True),
    ("Amul Cheese Slices 200g", "Dairy", 130, 90, False),
    ("Nestle a+ Milk 500ml", "Dairy", 35, 3, True),
    ("Amul Gold Milk 500ml", "Dairy", 34, 3, True),
    ("Paneer 200g", "Dairy", 95, 4, True),
    ("Amul Lassi 200ml", "Dairy", 25, 4, True),
    ("Britannia Cheese 200g", "Dairy", 120, 60, False),
    ("Amul Ghee 500ml", "Dairy", 320, 365, False),
    # Packaged Foods
    ("Maggi Noodles 70g", "Packaged Foods", 14, 365, False),
    ("Lays Classic 26g", "Packaged Foods", 20, 180, False),
    ("Parle-G Biscuits 799g", "Packaged Foods", 90, 180, False),
    ("Britannia Marie Gold 300g", "Packaged Foods", 42, 180, False),
    ("Aashirvaad Atta 5kg", "Packaged Foods", 280, 180, False),
    ("Tata Salt 1kg", "Packaged Foods", 28, 365, False),
    ("Fortune Sunflower Oil 1L", "Packaged Foods", 155, 365, False),
    ("Saffola Gold Oil 1L", "Packaged Foods", 185, 365, False),
    ("Kissan Jam 500g", "Packaged Foods", 120, 365, False),
    ("Maggi Ketchup 500g", "Packaged Foods", 105, 365, False),
    ("Haldiram Bhujia 200g", "Packaged Foods", 80, 180, False),
    ("Kurkure Masala 65g", "Packaged Foods", 20, 180, False),
    ("Hide & Seek 100g", "Packaged Foods", 35, 180, False),
    ("Sunfeast Dark Fantasy 75g", "Packaged Foods", 30, 180, False),
    ("Amul Dark Chocolate 150g", "Dairy", 220, 365, False),
    # Beverages
    ("Coca Cola 750ml", "Beverages", 45, 365, False),
    ("Pepsi 750ml", "Beverages", 42, 365, False),
    ("Red Bull 250ml", "Beverages", 135, 365, False),
    ("Tropicana Orange 1L", "Beverages", 99, 30, False),
    ("Real Mango Juice 1L", "Beverages", 95, 30, False),
    ("Bisleri Water 1L", "Beverages", 20, 365, False),
    ("Kinley Soda 750ml", "Beverages", 30, 365, False),
    ("Chaayos Masala Tea 250g", "Beverages", 299, 365, False),
    ("Nescafe Classic 50g", "Beverages", 180, 365, False),
    ("Horlicks 500g", "Beverages", 290, 365, False),
    # Personal Care
    ("Dove Soap 100g", "Personal Care", 55, 730, False),
    ("Head & Shoulders 180ml", "Personal Care", 199, 730, False),
    ("Colgate Strong Teeth 200g", "Personal Care", 88, 730, False),
    ("Dettol Handwash 200ml", "Personal Care", 89, 730, False),
    ("Vaseline Lotion 200ml", "Personal Care", 149, 730, False),
    ("Whisper Ultra 7pcs", "Personal Care", 55, 730, False),
    ("Gillette Mach3 2pcs", "Personal Care", 199, 730, False),
    ("Biotique Facewash 100ml", "Personal Care", 110, 730, False),
    ("Nivea Cream 100ml", "Personal Care", 139, 730, False),
    ("Pantene Shampoo 340ml", "Personal Care", 259, 730, False),
    # Household
    ("Vim Dishwash Bar 200g", "Household", 22, 730, False),
    ("Surf Excel 500g", "Household", 95, 730, False),
    ("Harpic Toilet Cleaner 500ml", "Household", 105, 730, False),
    ("Good Knight Liquid 45ml", "Household", 99, 365, False),
    ("Lizol Floor Cleaner 500ml", "Household", 109, 730, False),
    ("Scotch-Brite Scrub Pad", "Household", 35, 730, False),
    ("Tissue Roll 150 pulls", "Household", 55, 730, False),
    ("Garbage Bags 30pcs", "Household", 75, 730, False),
    # Frozen/Ready to Eat
    ("McCain French Fries 400g", "Frozen Foods", 165, 180, False),
    ("Wow Momos Veg 400g", "Frozen Foods", 140, 60, False),
    ("Fresho Paneer Tikka 250g", "Frozen Foods", 180, 30, True),
    ("ITC Master Chef Veg Biryani 250g", "Frozen Foods", 95, 30, True),
    # Breakfast
    ("Kellogg's Corn Flakes 500g", "Breakfast", 200, 365, False),
    ("Quaker Oats 500g", "Breakfast", 145, 365, False),
    ("Britannia Bread 400g", "Breakfast", 40, 5, True),
    ("Brown Bread 400g", "Breakfast", 48, 5, True),
    ("Bonn Pav 6pcs", "Breakfast", 35, 3, True),
]

# ── Dark stores (Mumbai simulation) ──────────────────────────────────────────
STORES = [
    {"store_id": "MUM001", "name": "Andheri West", "lat": 19.1364, "lng": 72.8296, "locality": "andheri"},
    {"store_id": "MUM002", "name": "Bandra East",  "lat": 19.0596, "lng": 72.8552, "locality": "bandra"},
    {"store_id": "MUM003", "name": "Powai",        "lat": 19.1176, "lng": 72.9060, "locality": "powai"},
    {"store_id": "MUM004", "name": "Malad West",   "lat": 19.1874, "lng": 72.8481, "locality": "malad"},
    {"store_id": "MUM005", "name": "Goregaon East","lat": 19.1663, "lng": 72.8526, "locality": "goregaon"},
]

# ── Indian festivals & events ─────────────────────────────────────────────────
FESTIVALS_2024 = {
    "2024-01-26": "Republic Day", "2024-03-25": "Holi",
    "2024-04-14": "Baisakhi",     "2024-10-02": "Gandhi Jayanti",
    "2024-10-12": "Navratri",     "2024-11-01": "Diwali",
    "2024-11-15": "Bhai Dooj",    "2024-12-25": "Christmas",
    "2024-12-31": "New Year Eve",
}

def get_demand_multiplier(date, category, store_locality):
    """Real demand patterns based on day, festival, weather"""
    multiplier = 1.0
    day = date.weekday()  # 0=Monday

    # Weekend surge
    if day == 5: multiplier *= 1.4
    if day == 6: multiplier *= 1.6

    # Morning rush (simulated as day-level)
    # Festival surge
    date_str = date.strftime("%Y-%m-%d")
    if date_str in FESTIVALS_2024:
        festival = FESTIVALS_2024[date_str]
        if "Holi" in festival:
            if category in ["Beverages", "Packaged Foods"]: multiplier *= 2.5
        if "Diwali" in festival:
            if category in ["Packaged Foods", "Personal Care"]: multiplier *= 3.0
        if "New Year Eve" in festival:
            if category == "Beverages": multiplier *= 2.8
        multiplier = max(multiplier, 1.8)  # General festival surge

    # Category-specific patterns
    if category == "Fruits & Vegetables":
        if day == 0: multiplier *= 1.2  # Monday restock
        if day == 5 or day == 6: multiplier *= 1.5
    if category == "Dairy":
        multiplier *= 1.1  # Daily staple
    if category == "Frozen Foods":
        if day == 4 or day == 5: multiplier *= 1.6  # Friday-Saturday

    # Locality wealth effect
    if store_locality in ["bandra", "powai"]: multiplier *= 1.3
    if store_locality == "malad": multiplier *= 0.9

    return round(multiplier, 2)

def generate_inventory_data():
    print("Generating inventory + sales data...")
    records = []
    start_date = datetime(2024, 1, 1)
    
    for store in STORES:
        print(f"  Store: {store['name']}")
        for product in PRODUCTS:
            name, category, mrp, shelf_life, is_perishable = product
            sku_id = f"SKU-{abs(hash(name)) % 100000:05d}"
            
            # Base daily demand (units sold per day)
            base_demand = random.randint(8, 50) if is_perishable else random.randint(3, 25)
            
            for day_offset in range(365):
                date = start_date + timedelta(days=day_offset)
                multiplier = get_demand_multiplier(date, category, store["locality"])
                
                # Add noise
                noise = np.random.normal(1.0, 0.15)
                units_sold = max(0, int(base_demand * multiplier * noise))
                
                # Stock ordered (sometimes over/under stocked — the real problem)
                if is_perishable:
                    # Perishables: often over-ordered (wastage problem)
                    order_bias = random.uniform(0.9, 1.4)
                else:
                    order_bias = random.uniform(0.95, 1.1)
                
                stock_ordered = max(0, int(units_sold * order_bias))
                waste = max(0, stock_ordered - units_sold) if is_perishable else 0
                
                # Revenue
                discount_pct = random.choice([0, 5, 10, 15, 20])
                sell_price = mrp * (1 - discount_pct/100)
                revenue = units_sold * sell_price
                waste_cost = waste * (mrp * 0.6)  # cost price ~60% of mrp
                
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "day_of_week": date.weekday(),
                    "month": date.month,
                    "is_weekend": 1 if date.weekday() >= 5 else 0,
                    "is_festival": 1 if date.strftime("%Y-%m-%d") in FESTIVALS_2024 else 0,
                    "festival_name": FESTIVALS_2024.get(date.strftime("%Y-%m-%d"), "none"),
                    "store_id": store["store_id"],
                    "store_name": store["name"],
                    "store_locality": store["locality"],
                    "sku_id": sku_id,
                    "product_name": name,
                    "category": category,
                    "mrp": mrp,
                    "sell_price": round(sell_price, 2),
                    "discount_pct": discount_pct,
                    "shelf_life_days": shelf_life,
                    "is_perishable": int(is_perishable),
                    "base_demand": base_demand,
                    "demand_multiplier": multiplier,
                    "units_sold": units_sold,
                    "stock_ordered": stock_ordered,
                    "waste_units": waste,
                    "revenue": round(revenue, 2),
                    "waste_cost": round(waste_cost, 2),
                })
    
    df = pd.DataFrame(records)
    df.to_csv(str(BASE_DIR / "data" / "inventory_history.csv"), index=False)
    print(f"✅ Generated {len(df):,} records")
    print(f"   Stores: {df['store_id'].nunique()}")
    print(f"   SKUs: {df['sku_id'].nunique()}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Total waste cost: ₹{df['waste_cost'].sum():,.0f}")
    return df

if __name__ == "__main__":
    df = generate_inventory_data()
    # Save store metadata
    with open(str(BASE_DIR / "data" / "stores.json"), "w") as f:
        json.dump(STORES, f, indent=2)
    print("\n✅ stores.json saved")
    print("\nSample data:")
    print(df[df['is_perishable']==1][['date','store_name','product_name','units_sold','stock_ordered','waste_units','waste_cost']].head(10).to_string())
