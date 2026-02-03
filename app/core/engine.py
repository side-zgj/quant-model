import pandas as pd
import numpy as np
from typing import Callable, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class Backtester:
    """
    Generic Backtesting Engine for quantitative strategies.
    
    Attributes:
        data (pd.DataFrame): Historical OHLCV data.
        initial_capital (float): Starting balance for the backtest.
    """

    def __init__(self, data: pd.DataFrame, initial_capital: float = 100000.0):
        self.data = data
        self.initial_capital = initial_capital
        self.results = {}

    def run(self, strategy_func: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series], **params) -> Dict[str, Any]:
        """
        Executes the backtest using a provided strategy function.

        Args:
            strategy_func: A function that takes data and params, returning a signal Series.
                           Signals: 1 (Buy), -1 (Sell), 0 (Hold).
            params: Dictionary of parameters for the strategy.

        Returns:
            Dict[str, Any]: Backtest metrics and performance summary.
        """
        logger.info(f"Running backtest with strategy: {strategy_func.__name__}")
        
        # 1. Generate signals (Ensure no look-ahead bias by shifting or using prev data)
        signals = strategy_func(self.data, params)
        
        # 2. Calculate daily returns
        # We assume execution at the next day's open or same day's close
        # To avoid look-ahead bias, signals generated today are executed tomorrow
        df = self.data.copy()
        df['signal'] = signals
        df['position'] = df['signal'].shift(1).fillna(0) # Position held during the day
        
        df['market_return'] = df['close'].pct_change()
        df['strategy_return'] = df['position'] * df['market_return']
        
        # 3. Calculate Equity Curve
        df['cumulative_return'] = (1 + df['strategy_return']).cumprod()
        df['equity'] = self.initial_capital * df['cumulative_return']
        
        # 4. Calculate Metrics
        metrics = self._calculate_metrics(df)
        
        self.results = {
            "metrics": metrics,
            "equity_curve": df[['equity', 'strategy_return']].reset_index().to_dict(orient='records'),
            "signals": df[['signal', 'position']].reset_index().to_dict(orient='records')
        }
        
        return self.results

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates performance metrics: Annualized Return, Max Drawdown, Sharpe Ratio, Win Rate.
        """
        # Annualized Return
        total_return = (df['equity'].iloc[-1] / self.initial_capital) - 1
        days = (df.index[-1] - df.index[0]).days
        if days <= 0:
            annualized_return = 0
        else:
            annualized_return = (1 + total_return) ** (365.25 / days) - 1

        # Max Drawdown
        rolling_max = df['equity'].cummax()
        drawdown = (df['equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Sharpe Ratio (Assuming 3% risk-free rate)
        rf = 0.03 / 252 # Daily risk-free rate
        excess_returns = df['strategy_return'] - rf
        if excess_returns.std() == 0:
            sharpe_ratio = 0
        else:
            sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

        # Win Rate (Percentage of positive return days)
        trades = df[df['strategy_return'] != 0]['strategy_return']
        win_rate = (trades > 0).mean() if len(trades) > 0 else 0

        return {
            "annualized_return": float(annualized_return),
            "max_drawdown": float(max_drawdown),
            "sharpe_ratio": float(sharpe_ratio),
            "win_rate": float(win_rate),
            "total_trades": int((df['signal'] != 0).sum())
        }

def example_sma_strategy(data: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
    """
    Example Simple Moving Average Crossover strategy.
    """
    short_window = params.get('short_window', 20)
    long_window = params.get('long_window', 50)
    
    sma_short = data['close'].rolling(window=short_window).mean()
    sma_long = data['close'].rolling(window=long_window).mean()
    
    signals = pd.Series(index=data.index, data=0)
    signals[sma_short > sma_long] = 1
    signals[sma_short < sma_long] = -1
    
    return signals
