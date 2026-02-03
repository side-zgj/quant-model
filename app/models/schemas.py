from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class OHLCV(BaseModel):
    """
    Standard OHLCV (Open, High, Low, Close, Volume) data model.
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None

class StrategyParams(BaseModel):
    """
    Parameters for a trading strategy.
    """
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0
    strategy_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BacktestResult(BaseModel):
    """
    Metrics and results of a backtest execution.
    """
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    trades_log: List[Dict[str, Any]] = Field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list)

class AgentQuery(BaseModel):
    """
    Model for AI Agent natural language queries.
    """
    query: str
