"""
Quantitative Opening Range Breakout (ORB) - Ablation Engine
Author: Jorge Neira
Description: 
Evaluates the marginal contribution of structural market filters (Delta, Excursion, 
and Retest Tolerance) on 1-minute OHLC index data.
"""

import pandas as pd
import numpy as np
from datetime import time

def clean_mt5_csv(file_path):
    """
    Reads and sanitizes institutional OHLCV data.
    Filters out missing ticks, zero-values, and normalizes timestamps.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 11:
                dt = parts[0]
                try:
                    op = float(parts[1] + '.' + parts[2])
                    hi = float(parts[3] + '.' + parts[4])
                    lo = float(parts[5] + '.' + parts[6])
                    cl = float(parts[7] + '.' + parts[8])
                    data.append([dt, op, hi, lo, cl])
                except ValueError:
                    continue
                    
    df = pd.DataFrame(data, columns=['Datetime', 'Open', 'High', 'Low', 'Close'])
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    df.sort_index(inplace=True)
    
    df = df[(df['High'] >= df['Low']) & (df['Open'] > 0) & (df['Close'] > 0)]
    df = df[~df.index.duplicated(keep='first')]
    return df

def calculate_metrics(trades):
    """
    Computes institutional performance metrics:
    Win Rate, Expectancy (R), Profit Factor, Sharpe Ratio, and Max Drawdown.
    """
    if not trades:
        return [0, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    trades_arr = np.array(trades)
    wins = trades_arr[trades_arr > 0]
    losses = trades_arr[trades_arr <= 0]
    
    total_trades = len(trades_arr)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    expectancy = np.mean(trades_arr)
    
    gross_profit = np.sum(wins) if len(wins) > 0 else 0
    gross_loss = np.abs(np.sum(losses)) if len(losses) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    sharpe = (np.mean(trades_arr) / np.std(trades_arr)) * np.sqrt(252) if np.std(trades_arr) > 0 else 0
    
    cum_r = np.cumsum(trades_arr)
    max_dd = np.max(np.maximum.accumulate(cum_r) - cum_r) if len(cum_r) > 0 else 0
    
    return [total_trades, round(win_rate * 100, 2), round(expectancy, 2), 
            round(profit_factor, 2), round(sharpe, 2), round(max_dd, 2)]

def run_ablation_matrix(file_path):
    """
    Executes the progressive component-level testing framework.
    Iterates through Naive ORB -> +Delta -> +Excursion -> Full Retest Model.
    """
    df = clean_mt5_csv(file_path)
    models = {
        'Model 1: Naive ORB': 1,
        'Model 2: ORB + Delta': 2,
        'Model 3: + Excursion': 3,
        'Model 4: Full Model': 4
    }
    results = []
    cutoff_time = time(13, 0)
    
    for model_name, m_type in models.items():
        trades = []
        for date, group in df.groupby(df.index.date):
            or_bars = group.between_time('09:30', '09:44')
            if len(or_bars) == 0: continue
            
            or_high = or_bars['High'].max()
            or_low = or_bars['Low'].min()
            
            delta = 0.25
            exc_pct = 0.0015
            tol_pct = 0.0005
            
            if m_type == 1:
                entry_L, entry_S = or_high, or_low
                risk_pts = or_high - or_low
            else:
                entry_L, entry_S = or_high + delta, or_low - delta
                risk_pts = entry_L - entry_S
                
            target_exc_L = entry_L * (1 + exc_pct)
            target_exc_S = entry_S * (1 - exc_pct)
            
            tol_upper_L = entry_L * (1 + tol_pct)
            tol_lower_L = entry_L * (1 - tol_pct)
            tol_upper_S = entry_S * (1 + tol_pct)
            tol_lower_S = entry_S * (1 - tol_pct)
            
            pos = entry_price = sl = tp = dir_exc = 0
            exc_reached = False
            
            trade_bars = group.between_time('09:45', '13:00')
            for row in trade_bars.itertuples():
                high, low, current_time = row.High, row.Low, row.Index.time()
                
                if pos == 0:
                    if m_type in [1, 2]:
                        if high >= entry_L:
                            pos, entry_price, sl, tp = 1, entry_L, entry_S, entry_L + (2 * risk_pts)
                        elif low <= entry_S:
                            pos, entry_price, sl, tp = -1, entry_S, entry_L, entry_S - (2 * risk_pts)
                    elif m_type in [3, 4]:
                        if not exc_reached:
                            if high >= target_exc_L: exc_reached, dir_exc = True, 1
                            elif low <= target_exc_S: exc_reached, dir_exc = True, -1
                            
                        if exc_reached:
                            if m_type == 3: 
                                if dir_exc == 1: pos, entry_price, sl, tp = 1, target_exc_L, entry_S, target_exc_L + (2 * risk_pts)
                                else: pos, entry_price, sl, tp = -1, target_exc_S, entry_L, target_exc_S - (2 * risk_pts)
                            elif m_type == 4: 
                                if dir_exc == 1 and low <= tol_upper_L and high >= tol_lower_L:
                                    pos, entry_price, sl, tp = 1, entry_L, entry_S, entry_L + (2 * risk_pts)
                                elif dir_exc == -1 and high >= tol_lower_S and low <= tol_upper_S:
                                    pos, entry_price, sl, tp = -1, entry_S, entry_L, entry_S - (2 * risk_pts)

                if pos != 0:
                    if m_type == 4: 
                        r_gained = (high - entry_price) / risk_pts if pos == 1 else (entry_price - low) / risk_pts
                        if r_gained >= 1.5:
                            sl = max(sl, entry_price + 0.5 * risk_pts) if pos == 1 else min(sl, entry_price - 0.5 * risk_pts)
                        elif r_gained >= 1.0:
                            sl = max(sl, entry_price) if pos == 1 else min(sl, entry_price)

                    if pos == 1:
                        if low <= sl: trades.append((sl - entry_price) / risk_pts); break
                        elif high >= tp: trades.append((tp - entry_price) / risk_pts); break
                    else:
                        if high >= sl: trades.append((entry_price - sl) / risk_pts); break
                        elif low <= tp: trades.append((entry_price - tp) / risk_pts); break
                        
                    if current_time >= cutoff_time:
                        trades.append((row.Close - entry_price) / risk_pts if pos == 1 else (entry_price - row.Close) / risk_pts)
                        break
                        
        metrics = calculate_metrics(trades)
        results.append([model_name] + metrics)
        
    return pd.DataFrame(results, columns=['Model', 'Total Trades', 'Win Rate (%)', 'Expectancy (R)', 'Profit Factor', 'Sharpe', 'Max Drawdown (R)'])

if __name__ == "__main__":
    # Ensure correct filepath for local execution
    file_path = '../data/sample_data_1m.csv'
    try:
        print(">>> Initializing Ablation Engine Matrix...")
        results = run_ablation_matrix(file_path)
        print("\n", results.to_string(index=False))
    except FileNotFoundError:
        print(f"[!] Target dataset '{file_path}' not found. Please verify the /data/ directory.")