# src/performance_optimization/parallel_access.py

import concurrent.futures


class ParallelAccessManager:
    def __init__(self, max_workers=4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_task(self, task, *args, **kwargs):
        return self.executor.submit(task, *args, **kwargs)

    def wait_for_tasks(self, futures):
        return concurrent.futures.wait(futures)

    def shutdown(self):
        self.executor.shutdown(wait=True)
