"""
ZeptoBrain — Demand Forecasting Model
Uses XGBoost to predict next-day/7-day demand per SKU per store
"""
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import pickle
import os
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent

MODEL_PATH = str(BASE_DIR / "ml" / "demand_model.pkl")
ENCODER_PATH = str(BASE_DIR / "ml" / "encoders.pkl")

def load_and_prepare_data():
    df = pd.read_csv(str(BASE_DIR / "data" / "inventory_history.csv"))
    df['date'] = pd.to_datetime(df['date'])
    
    # Feature engineering
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['quarter'] = df['date'].dt.quarter
    df['day_of_month'] = df['date'].dt.day
    
    # Lag features — yesterday's and last week's sales
    df = df.sort_values(['store_id', 'sku_id', 'date'])
    df['lag_1'] = df.groupby(['store_id','sku_id'])['units_sold'].shift(1)
    df['lag_7'] = df.groupby(['store_id','sku_id'])['units_sold'].shift(7)
    df['rolling_7_mean'] = df.groupby(['store_id','sku_id'])['units_sold'].transform(
        lambda x: x.shift(1).rolling(7, min_periods=1).mean()
    )
    df['rolling_7_std'] = df.groupby(['store_id','sku_id'])['units_sold'].transform(
        lambda x: x.shift(1).rolling(7, min_periods=1).std().fillna(0)
    )
    
    df = df.dropna(subset=['lag_1','lag_7'])
    return df

def train_model():
    print("Loading data...")
    df = load_and_prepare_data()
    
    # Encode categoricals
    encoders = {}
    for col in ['store_id', 'sku_id', 'category', 'store_locality']:
        le = LabelEncoder()
        df[col+'_enc'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    
    FEATURES = [
        'store_id_enc', 'sku_id_enc', 'category_enc', 'store_locality_enc',
        'day_of_week', 'month', 'week_of_year', 'quarter', 'day_of_month',
        'is_weekend', 'is_festival', 'is_perishable',
        'mrp', 'discount_pct', 'shelf_life_days', 'base_demand',
        'lag_1', 'lag_7', 'rolling_7_mean', 'rolling_7_std',
        'demand_multiplier'
    ]
    
    X = df[FEATURES]
    y = df['units_sold']
    
    # Time-based split (train on first 10 months, test on last 2)
    split_date = pd.to_datetime("2024-11-01")
    train_mask = df['date'] < split_date
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]
    
    print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")
    
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    
    print("Training XGBoost model...")
    model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              verbose=False)
    
    preds = model.predict(X_test)
    preds = np.maximum(preds, 0)  # no negative demand
    
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mape = np.mean(np.abs((y_test - preds) / (y_test + 1))) * 100
    
    print(f"\n📊 Model Performance:")
    print(f"   MAE:  {mae:.2f} units")
    print(f"   RMSE: {rmse:.2f} units")
    print(f"   MAPE: {mape:.1f}%")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': FEATURES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print(f"\n🔑 Top 5 Features:")
    print(importance.head(5).to_string(index=False))
    
    # Save
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump({'model': model, 'features': FEATURES}, f)
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(encoders, f)
    
    print(f"\n✅ Model saved to {MODEL_PATH}")
    return model, encoders, FEATURES, df

def predict_demand(store_id, sku_id, days_ahead=7, df_history=None):
    """Predict demand for next N days for a given store+SKU"""
    with open(MODEL_PATH, 'rb') as f:
        payload = pickle.load(f)
    model, features = payload['model'], payload['features']
    
    with open(ENCODER_PATH, 'rb') as f:
        encoders = pickle.load(f)
    
    if df_history is None:
        df_history = pd.read_csv(str(BASE_DIR / "data" / "inventory_history.csv"))
        df_history['date'] = pd.to_datetime(df_history['date'])
    
    # Get last known row for this store+SKU
    mask = (df_history['store_id'] == store_id) & (df_history['sku_id'] == sku_id)
    sku_data = df_history[mask].sort_values('date').tail(7)
    
    if sku_data.empty:
        return []
    
    last_row = sku_data.iloc[-1]
    last_date = pd.to_datetime(last_row['date'])
    
    predictions = []
    recent_sales = list(sku_data['units_sold'].values)
    
    for i in range(days_ahead):
        pred_date = last_date + pd.Timedelta(days=i+1)
        
        row = {
            'store_id_enc': encoders['store_id'].transform([store_id])[0] if store_id in encoders['store_id'].classes_ else 0,
            'sku_id_enc': encoders['sku_id'].transform([sku_id])[0] if sku_id in encoders['sku_id'].classes_ else 0,
            'category_enc': encoders['category'].transform([last_row['category']])[0],
            'store_locality_enc': encoders['store_locality'].transform([last_row['store_locality']])[0],
            'day_of_week': pred_date.weekday(),
            'month': pred_date.month,
            'week_of_year': pred_date.isocalendar()[1],
            'quarter': (pred_date.month - 1) // 3 + 1,
            'day_of_month': pred_date.day,
            'is_weekend': 1 if pred_date.weekday() >= 5 else 0,
            'is_festival': 0,
            'is_perishable': last_row['is_perishable'],
            'mrp': last_row['mrp'],
            'discount_pct': last_row['discount_pct'],
            'shelf_life_days': last_row['shelf_life_days'],
            'base_demand': last_row['base_demand'],
            'lag_1': recent_sales[-1] if recent_sales else last_row['units_sold'],
            'lag_7': recent_sales[-7] if len(recent_sales) >= 7 else last_row['units_sold'],
            'rolling_7_mean': np.mean(recent_sales[-7:]) if recent_sales else last_row['units_sold'],
            'rolling_7_std': np.std(recent_sales[-7:]) if len(recent_sales) > 1 else 0,
            'demand_multiplier': 1.4 if pred_date.weekday() >= 5 else 1.0,
        }
        
        X = pd.DataFrame([row])[features]
        pred = max(0, int(model.predict(X)[0]))
        
        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "day": pred_date.strftime("%A"),
            "predicted_units": pred,
            "is_weekend": bool(pred_date.weekday() >= 5)
        })
        recent_sales.append(pred)
    
    return predictions

if __name__ == "__main__":
    model, encoders, features, df = train_model()
    
    # Test prediction
    print("\n🔮 Sample 7-day forecast:")
    test_store = "MUM001"
    test_sku = df[df['store_id']==test_store]['sku_id'].iloc[0]
    test_product = df[df['sku_id']==test_sku]['product_name'].iloc[0]
    
    preds = predict_demand(test_store, test_sku, days_ahead=7, df_history=df)
    print(f"   Product: {test_product} | Store: {test_store}")
    for p in preds:
        print(f"   {p['date']} ({p['day'][:3]}): {p['predicted_units']} units")
