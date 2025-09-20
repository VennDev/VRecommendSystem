from prometheus_client import Counter

TOTAL_RUNNING_TASKS = Counter(
    'total_running_tasks',
    'Total number of tasks currently running'
)

TOTAL_COUNT_RUN_TASKS = Counter(
    'total_count_run_tasks',
    'Total number of tasks that have been run'
)

RUNTIME = Counter(
    'task_runtime_seconds',
    'Total runtime of tasks in seconds'
)
