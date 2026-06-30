def calc_spec_31(raw_data):
    if raw_data is None:
        return -31.0
    import numpy as np
    try:
        if raw_data.ndim != 2 or raw_data.shape[1] < 2:
            return -31.1
        t = raw_data[:, 0]
        v = raw_data[:, 1]
        mask = ~np.isnan(t) & ~np.isnan(v)
        t = t[mask]
        v = v[mask]
        n = len(t)
        if n < 10:
            return -31.2
        t_steady = t[n // 2:]
        v_steady = v[n // 2:]
        v_ac = v_steady - np.mean(v_steady)
        zero_cross = np.where(np.diff(np.sign(v_ac)))[0]
        if len(zero_cross) < 3:
            return -31.3
        t_cross = t_steady[zero_cross]
        periods = np.diff(t_cross[::2])
        if len(periods) == 0:
            return -31.4
        freq = 1.0 / np.mean(periods)
        return float(freq)
    except Exception:
        return -31.5