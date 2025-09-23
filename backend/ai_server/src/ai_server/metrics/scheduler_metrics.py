from prometheus_client import Gauge

TOTAL_RUNNING_TASKS = Gauge(
    'total_running_tasks',
    'Total number of tasks currently running'
)

TOTAL_COUNT_RUN_TASKS = Gauge(
    'total_count_run_tasks',
    'Total number of tasks that have been run'
)

TOTAL_ACTIVATED_TASKS = Gauge(
    'total_activated_tasks',
    'Total number of tasks that have been activated'
)

TASK_RUNTIME_SECONDS = Gauge(
    'task_runtime_seconds',
    'Total runtime of tasks in seconds'
)
