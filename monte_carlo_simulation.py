"""
Quantitative Opening Range Breakout (ORB) - Tail Risk & Monte Carlo Simulation
Author: Jorge Neira
Description: 
Executes a Bootstrap Monte Carlo simulation (with replacement) on a sequence 
of trade outcomes to model empirical tail risk, Maximum Drawdown probabilities, 
and consecutive loss clusters for institutional position sizing.
"""

import numpy as np
import pandas as pd

def calculate_drawdown(equity_curve):
    """
    Calculates the Maximum Drawdown (Peak-to-Trough) of a given equity curve.
    Returns the max drawdown in R-multiples.
    """
    peak = np.maximum.accumulate(equity_curve)
    drawdown = peak - equity_curve
    return np.max(drawdown)

def calculate_max_losing_streak(trades):
    """
    Calculates the maximum number of consecutive losing trades in a sequence.
    """
    is_loss = trades <= 0
    # Create an array that resets to 0 on wins and increments on losses
    streak = is_loss * (np.cumsum(is_loss) - np.maximum.accumulate(np.cumsum(is_loss) * (~is_loss)))
    return np.max(streak)

def run_monte_carlo_simulation(trades, iterations=5000):
    """
    Runs a Bootstrap Monte Carlo simulation with replacement.
    Evaluates tail risk metrics over 'n' iterations.
    """
    if len(trades) == 0:
        raise ValueError("Trade sequence is empty.")

    print(f">>> Initializing Bootstrap Monte Carlo ({iterations} iterations)...")
    
    max_drawdowns = np.zeros(iterations)
    max_losing_streaks = np.zeros(iterations)
    trade_count = len(trades)
    
    for i in range(iterations):
        # Randomly resample the trade sequence with replacement
        resampled_trades = np.random.choice(trades, size=trade_count, replace=True)
        equity_curve = np.cumsum(resampled_trades)
        
        max_drawdowns[i] = calculate_drawdown(equity_curve)
        max_losing_streaks[i] = calculate_max_losing_streak(resampled_trades)
        
    # Calculate statistical percentiles (Tail Risk)
    mean_dd = np.mean(max_drawdowns)
    p95_dd = np.percentile(max_drawdowns, 95)
    p99_dd = np.percentile(max_drawdowns, 99)
    
    mean_streak = np.mean(max_losing_streaks)
    p95_streak = np.percentile(max_losing_streaks, 95)
    p99_streak = np.percentile(max_losing_streaks, 99)
    
    # Format and return institutional risk report
    report = (
        f"{'='*50}\n"
        f" MONTE CARLO TAIL-RISK ANALYSIS\n"
        f"{'='*50}\n"
        f"Iterations:          {iterations}\n"
        f"Sample Size (N):     {trade_count} trades\n\n"
        f"--- MAXIMUM DRAWDOWN (R) ---\n"
        f"Mean Expected DD:    -{mean_dd:.2f} R\n"
        f"95th Percentile:     -{p95_dd:.2f} R (Severe Tail Risk)\n"
        f"99th Percentile:     -{p99_dd:.2f} R (Extreme Tail Risk)\n\n"
        f"--- CONSECUTIVE LOSSES ---\n"
        f"Mean Max Streak:     {mean_streak:.1f} trades\n"
        f"95th Percentile:     {p95_streak:.0f} trades\n"
        f"99th Percentile:     {p99_streak:.0f} trades\n"
        f"{'='*50}\n"
    )
    
    return report

if __name__ == "__main__":
    # Synthetic generation of the Out-Of-Sample trade profile for demonstration.
    # Matches the ~50-60% win rate and 1.7+ Profit Factor established in the study.
    np.random.seed(42) # Fixed seed for reproducibility in the public repository
    
    # Synthetic parameters based on the study's Full Model empirical metrics
    n_trades = 949 
    win_rate = 0.58
    
    # Generate an array representing a sequence of R-multiple returns
    # Wins average +1.5R (due to trailing stop), Losses are capped at -1.0R
    simulated_wins = np.random.normal(loc=1.5, scale=0.3, size=int(n_trades * win_rate))
    simulated_losses = np.clip(np.random.normal(loc=-1.0, scale=0.1, size=int(n_trades * (1 - win_rate))), -1.2, -0.5)
    
    historical_sequence = np.concatenate([simulated_wins, simulated_losses])
    np.random.shuffle(historical_sequence) # Shuffle to create realistic sequential distribution
    
    try:
        risk_report = run_monte_carlo_simulation(historical_sequence, iterations=5000)
        print(risk_report)
    except Exception as e:
        print(f"[!] Simulation failed: {e}")