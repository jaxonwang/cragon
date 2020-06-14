import time
import json
import os
import csv
import itertools

from cragon import monitor
from . import integrated_test


def valid_system_metrics(file_path):
    timestamp = ["timestamp"]
    base_metrics = "guest,guest_nice,idle,iowait,irq,nice,softirq,steal,system,user"
    base_metrics = base_metrics.split(",")
    cpu_metrics = [["cpu%d_%s" % (i, m) for m in base_metrics]
                   for i in range(os.cpu_count())]
    cpu_metrics = list(itertools.chain(*cpu_metrics))
    memory_metrics = "mem_active,mem_available,mem_buffers,mem_cached,mem_free,mem_inactive,mem_percent,mem_shared,mem_slab,mem_total,mem_used"
    memory_metrics = memory_metrics.split(",")

    all_metrics = cpu_metrics + memory_metrics + timestamp

    with open(file_path, "r") as f:
        reader = csv.reader(f)
        headers = next(reader, [])
        assert set(headers) == set(all_metrics)
        for row in reader:
            assert len(row) == len(all_metrics)


def valid_process_metrics(file_path):
    timestamp = ["timestamp"]
    mem = [
        "iowait",
        "rss",
        "vms",
        "shared",
        "text",
        "lib",
        "data",
        "dirty",
        "uss",
        "pss",
        "swap"]
    cpu = ["user", "system", "iowait"]
    all_metrics = timestamp + mem + cpu

    with open(file_path, "r") as f:
        for line in f:
            metrics = json.loads(line)
            keys = set([k.split("_")[-1] for k in metrics.keys()])
            for m in all_metrics:
                assert m in keys


def test_metric_monitor(tmpdir):
    m = monitor.MetricMonitor(0.1, tmpdir)

    m.start()
    time.sleep(0.4)
    m.stop()

    valid_system_metrics(integrated_test.get_system_metrics_log_path(tmpdir))


def test_metrics(tmpdir, capfd, print_log_if_fail):
    binary_path = os.path.join(
        integrated_test.test_cases_dir,
        "checkpoint",
        "pi_est.py")

    cmd = ["run", "-w", str(tmpdir), "python", binary_path, "1000000"]
    ret = integrated_test.run_cragon_cli(cmd)
    assert ret.returncode == 0

    valid_system_metrics(integrated_test.get_system_metrics_log_path(tmpdir))
    valid_process_metrics(integrated_test.get_process_metrics_log_path(tmpdir))
