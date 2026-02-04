import asyncio
import pandas as pd
import akshare as ak
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    """
    Asynchronous data pipeline for fetching financial market data.
    Includes retry mechanisms and exception handling.
    """

    def __init__(self, source: str = "akshare"):
        self.source = source

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def fetch_stock_daily(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        Fetches daily stock OHLCV data.

        Args:
            symbol (str): Stock ticker symbol (e.g., 'sh600000').
            start_date (str): Start date in 'YYYYMMDD' format.
            end_date (str): End date in 'YYYYMMDD' format.
            adjust (str): Adjustment type: 'qfq' (Forward), 'hfq' (Backward), or '' (None).

        Returns:
            pd.DataFrame: Stock historical data.

        Raises:
            Exception: If data fetching fails after retries.
        """
        logger.info(f"Fetching data for {symbol} from {start_date} to {end_date} (Adjust: {adjust})")
        
        # Clean symbol: AkShare expects '000001' not 'sz000001'
        clean_symbol = ''.join(filter(str.isdigit, symbol))
        
        try:
            # Using asyncio.to_thread to run synchronous akshare calls without blocking the event loop
            df = await asyncio.to_thread(
                ak.stock_zh_a_hist, 
                symbol=clean_symbol, 
                period="daily", 
                start_date=start_date, 
                end_date=end_date, 
                adjust=adjust
            )
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            # Robust column mapping using rename instead of direct assignment
            rename_map = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'pct_chg',
                '涨跌额': 'change',
                '换手率': 'turnover'
            }
            df = df.rename(columns=rename_map)
            
            # Ensure 'date' column exists
            if 'date' not in df.columns:
                # Fallback: if rename failed, try to use the first column as date
                logger.warning(f"Column 'date' not found, columns are: {df.columns.tolist()}")
                if '日期' in df.columns: # Should have been renamed
                    pass 
                else:
                    df.rename(columns={df.columns[0]: 'date'}, inplace=True)

            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise e

    async def get_multi_stocks(self, symbols: list, start_date: str, end_date: str):
        """
        Fetches data for multiple stocks concurrently.
        """
        tasks = [self.fetch_stock_daily(s, start_date, end_date) for s in symbols]
        return await asyncio.gather(*tasks, return_exceptions=True)
