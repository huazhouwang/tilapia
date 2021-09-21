import time
from typing import Callable

from wallet.lib.basic.functional.wraps import timeout_lock
from wallet.lib.basic.orm import database as orm_database
from wallet.lib.basic.orm.migrate import manager as migrate_manager
from wallet.lib.price import manager as price_manager
from wallet.lib.transaction import manager as transaction_manager


class Migrate:
    URI = "migrate"

    def on_post(self, req, resp):
        migrate_manager.migrating(orm_database.db)


class Ticker:
    URI = "tick/{task_name}"

    TASKS = {
        "price": price_manager.on_ticker_signal,
        "transaction": transaction_manager.on_ticker_signal,
    }

    def on_post(self, req, resp, task_name):
        tasks = self.TASKS
        queue = tasks.keys() if task_name == "all" else (task_name,)

        statistics = [
            {"task": task_name, "statistic": self._statistic(task_name, tasks[task_name])}
            for task_name in queue
            if task_name in tasks
        ]
        resp.media = statistics

    @staticmethod
    def _statistic(task_name: str, task: Callable):
        result = {}
        start_time = time.time()

        try:
            with timeout_lock(f"api.ticker.run_{task_name}", raise_if_timeout=True):
                result["receipt"] = task()
        except Exception as e:
            result["error"] = repr(e)
        finally:
            end_time = time.time()
            result["time_used"] = int(end_time - start_time)

        return result
