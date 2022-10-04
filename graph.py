import matplotlib.pyplot as plt
import numpy as np
from math import ceil


def mergeData(series_dict, replacement_dict):
    for new_name, vars_dict in replacement_dict.items():
        merged_data = None
        if "xname" in vars_dict and "yname" in vars_dict:
            X = series_dict.pop(vars_dict["xname"])
            Y = series_dict.pop(vars_dict["yname"])
            if X is not None and Y is not None:
                data = []
                # keep track of which index was used last
                current_indices = [-1, -1]
                # make ordered list of all timestamps between both data sets, no repeats
                all_timestamps = sorted(set(X[:, 0]).union(set(Y[:, 0])))
                for ts in all_timestamps:
                    # for each dimension (X & Y), index where timestamp exists, if timestamp exists. Else None 
                    ts_indices = tuple(indx[-1] if len(indx := np.where(Z[:, 0] == ts)[0]) > 0 else None
                                        for Z in (X, Y))
                    # Out of range timesteps assumed to be zero
                    ts_vals = [0, 0]
                    for variable_indx, (current_z_indx, Z) in enumerate(zip(ts_indices, (X, Y))):
                        last_index_used = current_indices[variable_indx]
                        if current_z_indx is not None:
                            # If timestep is present, get value
                            current_indices[variable_indx] = current_z_indx
                            ts_vals[variable_indx] = Z[current_z_indx, 1]
                        elif last_index_used not in (-1, len(Z[:, 0]) - 1):
                            # If timestep within range of data, linearly interpolate
                            t0, z0 = Z[last_index_used, :]
                            t1, z1 = Z[last_index_used + 1, :]
                            ts_vals[variable_indx] = z0 + (z1 - z0) * (ts - t0) / (t1 - t0)
                    data.append([ts, *ts_vals])
                merged_data = np.array(data)
            elif X is not None or Y is not None:
                vars_array = X if Y is None else Y
                zeros_index = 1 if Y is None else 2
                zeros_col = np.zeros(vars_array[:,0].size)
                merged_data = np.insert(vars_array, zeros_index, zeros_col, axis=1)
        elif "neg" in vars_dict and "pos" in vars_dict:
            Neg = series_dict.pop(vars_dict["neg"])
            Pos = series_dict.pop(vars_dict["pos"])
            if Neg is not None and Pos is not None:
                Neg[:, 1] *= -1
                merged_data = np.append(Pos, Neg, axis=0)
                merged_data = merged_data[merged_data[:, 0].argsort()]
            elif Neg is not None or Pos is not None:
                vars_array = Neg if Pos is None else Pos
                if Pos is None:
                    vars_array[:, 1] *= -1
                merged_data = vars_array
        series_dict[new_name] = merged_data

def graphEvents(time_series, end_time, num_cols=6):
    # Reformat Data
    adj_series = {key: (np.array(value) if value else None) for key, value in time_series.items()}
    mergeData(adj_series, {
        "LStick": {"xname": "LXStick", "yname": "LYStick"},
        "RStick": {"xname": "RXStick", "yname": "RYStick"},
        "XDpad": {"neg": "LDpad", "pos": "RDpad"},
        "YDpad": {"neg": "DDpad", "pos": "UDpad"}
    })
    # Plot Data
    num_widgets = len(adj_series)
    fig, axes = plt.subplots(ceil(num_widgets/num_cols), num_cols)
    fig.set_size_inches(10, 5)
    for num, (widget, points) in enumerate(adj_series.items()):
        ax = axes[num//num_cols, num%num_cols]
        ax.title.set_text(widget)
        if points is not None:
            if "Stick" in widget and "Click" not in widget:
                X, Y = tuple(points[:,i] for i in range(1,3))
                ax.plot(X, Y)
            elif "Trigger" in widget:
                X, Y = tuple(points[:,i] for i in range(2))
                ax.plot(X, Y)
            else:
                X, Y = tuple(points[:,i] for i in range(2))
                X = np.append(X, end_time)
                Y = np.append(Y, Y[-1])
                print(X,Y)
                ax.step(X, Y, where='post')
        else:
            ax.set_xlim([0, 5])
            ax.set_ylim([-1, 1])
            ax.text(1, 0, "No Data")
    for num in range(num_widgets, ceil(num_widgets/num_cols)*num_cols):
        fig.delaxes(axes[num//num_cols, num%num_cols])
    plt.tight_layout()
    plt.show()