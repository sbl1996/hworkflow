import re

import numpy as np
from toolz.curried import curry
from datetime import timedelta
from dateutil.parser import parse

def dtime(end, start):
    end = parse(end)
    start = parse(start)
    return end - start


@curry
def parse_metric_line(s):
    try:
        end_time = re.search(r"""^(\d{2}:\d{2}:\d{2})""", s).group(1)
        metrics = re.findall(r"""([a-zA-Z0-9]{2,5}): (\d+\.\d{4})""", s)
        return end_time, metrics
    except AttributeError as e:
        print(s)
        raise e

def parse_metric_lines(lines):
    times = []
    metrics = []
    for l in lines:
        if l:
            times_l, metrics_l = parse_metric_line(l)
        else:
            times_l, metrics_l = None, []
        times.append(times_l)
        metrics.append(metrics_l)
    metric_names = set([m[0] for ms in metrics for m in ms if m])
    d = {
        m: [-1] * len(lines) for m in metric_names
    }
    for i, ms in enumerate(metrics):
        for k, v in ms:
            d[k][i] = float(v)
    d = {
        k: np.array(v) for k, v in d.items()
    }
    d['time'] = times
    return d


def _parse(content):
    lines = content.splitlines()
    train_start = lines[0][:8]
    train_lines = []
    valid_lines = []

    cur_epoch_lines = []
    for l in lines:
        if l.startswith("Epoch"):
            if len(cur_epoch_lines) == 1:
                train_lines.append(cur_epoch_lines[0])
                valid_lines.append(None)
            elif len(cur_epoch_lines) == 2:
                train_lines.append(cur_epoch_lines[0])
                valid_lines.append(cur_epoch_lines[1])
            cur_epoch_lines = []
        elif ' train ' in l or 'valid' in l:
            cur_epoch_lines.append(l)
    if len(cur_epoch_lines) == 1:
        train_lines.append(cur_epoch_lines[0])
        valid_lines.append(None)
    elif len(cur_epoch_lines) == 2:
        train_lines.append(cur_epoch_lines[0])
        valid_lines.append(cur_epoch_lines[1])

    train_metrics = parse_metric_lines(train_lines)
    valid_metrics = parse_metric_lines(valid_lines)

    train_ends, valid_ends = train_metrics['time'], valid_metrics['time']
    for i in range(len(train_ends)):
        if valid_ends[i] is None:
            valid_ends[i] = train_ends[i]

    return train_start, train_metrics, valid_metrics


def estimate_epoch_train_time(train_ends, valid_ends):
    times = []
    for train_end, valid_end in zip(train_ends[1:], valid_ends[:-1]):
        times.append(dtime(train_end, valid_end).seconds)
    return np.mean(times).item()


def parse_log(content, key, mode='all'):
    assert mode in ["final", "max", "all"]

    train_start, train_metrics, valid_metrics = _parse(content)
    epoch_train_time = estimate_epoch_train_time(train_metrics['time'], valid_metrics['time'])
    total_cost = timedelta(seconds=dtime(valid_metrics['time'][-1], train_start).seconds)
    main_valid_metrics = valid_metrics[key] * 100
    train_losses = train_metrics['loss']

    final_metric = main_valid_metrics[-1]
    final_loss = train_losses[-1]
    max_metric = main_valid_metrics.max()
    max_metric_loss = train_losses[main_valid_metrics.argmax() - len(main_valid_metrics)]
    total_epochs = len(train_losses)
    epoch_time = (dtime(train_metrics['time'][-1], train_metrics['time'][0]).seconds / (total_epochs - 1))

    if mode == 'final':
        return f"%.2f %.4f %s %.1f %.1f" % (
            final_metric, final_loss, total_cost, epoch_time, epoch_train_time)
    elif mode == 'max':
        return f"%.2f %.4f %s %.1f %.1f" % (
            max_metric, max_metric_loss, total_cost, epoch_time, epoch_train_time)
    else:
        return "%.2f(%.2f) %.4f(%.4f) %s %.1f %.1f" % (
            final_metric, max_metric, final_loss, max_metric_loss, total_cost, epoch_time, epoch_train_time)
