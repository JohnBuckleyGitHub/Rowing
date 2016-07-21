import matplotlib.pyplot as plt


class gen_plot(object):
    def __init__(self, base_dict, channel_list, plot=True):
        self.chan_list = channel_list
        self.chan_count = len(self.chan_list)
        self.plot_count = self.chan_count - 1
        self.axes = (None,) * self.plot_count
        self.fig, self.axes = plt.subplots(nrows=(self.plot_count))
        if self.plot_count == 1:
            self.axes = [self.axes]
        self.channels = {}
        for chan in self.chan_list:
            self.channels[chan] = base_dict[chan]
        for i in range(1, self.chan_count):
            cl = self.chan_list
            ax = self.axes[i-1]
            ax.plot(self.channels[cl[0]], self.channels[cl[i]])
            ax.set_xlabel(cl[0])
            ax.set_ylabel(cl[i])
        if plot:
            plt.show()
