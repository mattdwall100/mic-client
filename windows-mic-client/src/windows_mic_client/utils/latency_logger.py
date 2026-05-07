import time
from contextlib import contextmanager
from logging import Logger


@contextmanager
def log_latency(logger: Logger, event_name: str, level: str = "info", **kwargs):
    # Custom context manager for starting and stopping timer and thn logging result
    # __enter__ code
    start_time = time.perf_counter()
    try:
        yield
    except Exception as e:
        # Error handler
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)

        # Add latency and error to the log string then construct full string
        kwargs["latency_ms"] = latency_ms
        kwargs["error"] = type(e).__name__
        kv_pairs = " ".join(f"{k}={v}" for k, v in kwargs.items())

        logger.error(f"{event_name}_failed | {kv_pairs}")
        raise e
    else:
        # __exit__ logic
        end_time = time.perf_counter()
        latency_ms = int((end_time - start_time) * 1000)

        # Build kwargs string
        kwargs["latency_ms"] = latency_ms
        kv_pairs = " ".join(f"{k}={v}" for k, v in kwargs.items())

        # callable logger.{level}
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"{event_name} | {kv_pairs}")
