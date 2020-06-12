import time
import os
import csv
import itertools

from cragon import monitor
from . import integrated_test


def test_metric_monitor(tmpdir):
    m = monitor.MetricMonitor(0.1, tmpdir)

    m.start()
    time.sleep(0.4)
    m.stop()

    timestamp = ["timestamp"]
    base_metrics = "guest,guest_nice,idle,iowait,irq,nice,softirq,steal,system,user"
    base_metrics = base_metrics.split(",")
    cpu_metrics = [["cpu%d_%s" % (i, m) for m in base_metrics]
                   for i in range(os.cpu_count())]
    cpu_metrics = list(itertools.chain(*cpu_metrics))
    memory_metrics = "mem_active,mem_available,mem_buffers,mem_cached,mem_free,mem_inactive,mem_percent,mem_shared,mem_slab,mem_total,mem_used"
    memory_metrics = memory_metrics.split(",")

    all_metrics = cpu_metrics + memory_metrics + timestamp

    with open(integrated_test.get_metrics_log_path(tmpdir), "r") as f:
        reader = csv.reader(f)
        headers = next(reader, [])
        assert set(headers) == set(all_metrics)
        for row in reader:
            assert len(row) == len(all_metrics)
