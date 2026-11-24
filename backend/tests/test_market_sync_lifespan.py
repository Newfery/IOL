import asyncio
import unittest
from unittest.mock import AsyncMock, call, patch

from src import app as app_module


class MarketSyncLifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_runs_yahoo_then_data912_sync_on_startup(self):
        calls = []

        async def run_sync(function):
            calls.append(function)
            if function is app_module.sync_yfinance_assets:
                return 0, 0, [], 500
            return 0, 0

        with patch(
            "src.app.asyncio.to_thread",
            new_callable=AsyncMock,
            side_effect=run_sync,
        ) as to_thread:
            async with app_module.lifespan(app_module.app):
                for _ in range(10):
                    if app_module.sync_data912_assets in calls:
                        break
                    await asyncio.sleep(0.01)

        sync_calls = [
            function
            for function in calls
            if function in (
                app_module.sync_yfinance_assets,
                app_module.sync_data912_assets,
            )
        ]
        self.assertEqual(sync_calls, [
            app_module.sync_yfinance_assets,
            app_module.sync_data912_assets,
        ])
        self.assertLess(
            to_thread.await_args_list.index(call(app_module.sync_yfinance_assets)),
            to_thread.await_args_list.index(call(app_module.sync_data912_assets)),
        )


if __name__ == "__main__":
    unittest.main()
