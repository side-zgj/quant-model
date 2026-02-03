from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import StrategyParams, BacktestResult, AgentQuery
from app.data.pipeline import DataPipeline
from app.core.engine import Backtester, example_sma_strategy
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
pipeline = DataPipeline()

@router.post("/backtest", response_model=Dict[str, Any])
async def run_backtest(params: StrategyParams):
    """
    Manually trigger a backtest with specific parameters.
    """
    logger.info(f"Received backtest request for {params.symbol}")
    
    try:
        # 1. Fetch data
        df = await pipeline.fetch_stock_daily(
            symbol=params.symbol,
            start_date=params.start_date,
            end_date=params.end_date
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the given parameters")
        
        # 2. Initialize Backtester
        tester = Backtester(df, initial_capital=params.initial_capital)
        
        # 3. Execute Strategy (Mapping name to function)
        strategies = {
            "SMA": example_sma_strategy
        }
        
        strat_func = strategies.get(params.strategy_name)
        if not strat_func:
            raise HTTPException(status_code=400, detail=f"Strategy {params.strategy_name} not implemented")
            
        result = tester.run(strat_func, **params.parameters)
        
        return result

    except Exception as e:
        logger.error(f"Backtest execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/query")
async def agent_interface(query: AgentQuery):
    """
    AI Agent interface: Converts natural language to strategy parameters.
    Uses Function Calling logic (Simulated here).
    """
    logger.info(f"AI Agent received query: {query.query}")
    
    # Simulated Function Calling Logic
    # In a real scenario, this would call an LLM (OpenAI, Claude, etc.) 
    # with a tool/function definition for 'run_backtest'.
    
    # Mocking the LLM response for a query like "用 20 和 50 日均线回测 600000 在 2023 年的表现"
    mock_params = {
        "symbol": "600000",
        "start_date": "20230101",
        "end_date": "20231231",
        "strategy_name": "SMA",
        "parameters": {
            "short_window": 20,
            "long_window": 50
        }
    }
    
    # Trigger the backtest using the parsed parameters
    try:
        params = StrategyParams(**mock_params)
        result = await run_backtest(params)
        return {
            "parsed_parameters": mock_params,
            "analysis": "Based on your request, I've executed an SMA crossover strategy for 600000.",
            "result": result
        }
    except Exception as e:
        return {"error": f"Failed to process agent query: {str(e)}"}
