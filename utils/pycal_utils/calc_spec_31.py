def calc_spec_31(raw_data):
    import numpy as np
    if raw_data is None:
        return -31.0
    try:
        if len(raw_data.shape) != 2 or raw_data.shape[1] < 2:
            return -31.1
        time = raw_data[:, 0]
        voltage = raw_data[:, 1]
        n = len(time)
        if n < 10:
            return -31.2
        start_idx = n // 2
        t_steady = time[start_idx:]
        v_steady = voltage[start_idx:]
        v_centered = v_steady - np.mean(v_steady)
        v_amp = np.max(v_centered) - np.min(v_centered)
        if v_amp < 0.001:
            return 0.0
        zero_crossings = np.where((v_centered[:-1] < 0) & (v_centered[1:] >= 0))[0]
        if len(zero_crossings) < 2:
            return -31.3
        t_cross = t_steady[zero_crossings] - v_centered[zero_crossings] * (t_steady[zero_crossings+1] - t_steady[zero_crossings]) / (v_centered[zero_crossings+1] - v_centered[zero_crossings])
        periods = np.diff(t_cross)
        if len(periods) == 0:
            return -31.4
        mean_period = np.mean(periods)
        if mean_period <= 0:
            return -31.5
        return float(1.0 / mean_period)
    except Exception:
        return -31.9