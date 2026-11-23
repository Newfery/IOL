import asyncio
import unittest
from unittest.mock import AsyncMock, call, patch

from src import app as app_module


class MarketSyncLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_runs_yahoo_sync_once_on_startup(self):
        async def run_sync(function):
            if function is app_module.sync_yfinance_assets:
                return 0, 0, [], 500
            return 0, 0

        with patch(
            "src.app.asyncio.to_thread",
            new_callable=AsyncMock,
            side_effect=run_sync,
        ) as to_thread:
            async with app_module.lifespan(app_module.app):
                await asyncio.sleep(0.01)

        self.assertEqual(
            to_thread.await_args_list.count(call(app_module.sync_yfinance_assets)),
            1,
        )


if __name__ == "__main__":
    unittest.main()
