#!/usr/bin/env python3

from PyQt5 import Qt, QtWidgets, uic
import sys
import time
import numpy as np
import numato_adc as nadc
import pyqtgraph as pg
import threading
import collections as col

ui_classes = uic.loadUiType('./numato_adc_gui.ui')
form_class = ui_classes[0]
base_class = ui_classes[1]

# Multithreading plot code based on:
# http://stackoverflow.com/questions/41156260/how-to-use-a-qthread-to-update-a-matplotlib-figure-with-pyqt

class NumatoAdcGui(base_class, form_class):
    send_fig = Qt.pyqtSignal(str)

    def __init__(self, parent=None, usbtmc=0):
        super().__init__()
        self.setupUi(self)

        self.adc_plot_curves = []
        for i in range(6):
            self.adc_plot_curves.append(self.adc_plot.plot())
            setattr(self, 'adc_plot_curve_%i' % i, self.adc_plot_curves[i])

        self._update_plot_timer = Qt.QTimer()
        self._update_plot_timer.timeout.connect(self.update)
        self.set_plot_update_time_s()
        self.replot_time_s.editingFinished.connect(self.set_plot_update_time_s)
        self.sample_rate_ms.editingFinished.connect(self.set_sample_rate_ms)
        self.data_buffer_size_samples.editingFinished.connect(self.set_data_buffer_size)
        self._timer_running = True
        self.start_stop.clicked.connect(self.toggle_update_plot_timer)

        # set plot defaults
        self.adc_plot.setLimits(yMin=0, yMax=10)

        # plotter and thread are none at the beginning
        self._data_buffer_size = int(self.data_buffer_size_samples.text())
        self._time_deque = col.deque([], self._data_buffer_size)
        self._data_deque = col.deque([], self._data_buffer_size)
        self.plotter = Plotter(self._data_buffer_size, float(self.sample_rate_ms.text()))
        self.thread = Qt.QThread()

        self.send_fig.connect(self.plotter.replot)
        self.plotter.return_fig.connect(self.plot)
        self.plotter.moveToThread(self.thread)
        self.thread.start()

    def closeEvent(self, event):
        self.plotter.get_data_flag = False
        super(Qt.QMainWindow, self).closeEvent(event)

    def toggle_update_plot_timer(self):
        if self._timer_running:
            self._timer_running = False
            self._update_plot_timer.stop()
        else:
            self._timer_running = True
            self.set_plot_update_time_s()

    def set_plot_update_time_s(self):
        self._ticker = self.replot_time_s.text()
        self._update_plot_timer.start(float(self._ticker)*1000.)

    def set_sample_rate_ms(self):
        self._sample_rate_ms = float(self.sample_rate_ms.text())
        self.plotter.sample_rate_ms = self._sample_rate_ms

    def set_data_buffer_size(self):
        data_buffer_size = int(self.data_buffer_size_samples.text())
        self._data_buffer_size = data_buffer_size
        time_deque = self._time_deque
        data_deque = self._data_deque
        self._time_deque = col.deque(time_deque, self._data_buffer_size)
        self._data_deque = col.deque(data_deque, self._data_buffer_size)
        self.plotter.data_buffer_size = data_buffer_size
        self.plotter.time_deque = col.deque(time_deque, self._data_buffer_size)
        self.plotter.data_deque = col.deque(data_deque, self._data_buffer_size)

    def update(self):
        self.send_fig.emit(self._ticker)

    def plot(self, time, data):
        self._time_deque.extend(time)
        self._data_deque.extend(data)
        active_plots = self.get_active_plots()
        active_idxs = np.where(active_plots)[0]
        for idx in active_idxs:
            self.adc_plot_curves[idx].setData(self._time_deque,
                                              self._data_deque+idx)

    def get_active_plots(self):
        active_plots_lst = []
        for i in range(6):
            active_plots_lst.append(getattr(self, 'adc_%i' % i).isChecked())
        return active_plots_lst

class Plotter(Qt.QObject):
    return_fig = Qt.pyqtSignal(object, object)

    def __init__(self, data_buffer_size, sample_rate_ms):
        Qt.QObject.__init__(self)

        self.start_time = time.time()
        self.data_buffer_size = data_buffer_size
        self.sample_rate_ms = sample_rate_ms
        self.time_deque = col.deque([], data_buffer_size)
        self.data_deque = col.deque([], data_buffer_size)
        self.get_data_flag = True
        self.data_thread = threading.Thread(target=self.get_data)
        self.data_thread.start()

    def get_data(self):
        while self.get_data_flag:
            self.time_deque.append(time.time()-self.start_time)
            self.data_deque.append(np.random.rand(1)[0])

    @Qt.pyqtSlot(str)
    def replot(self, ticker):
        time_deque = self.time_deque
        data_deque = self.data_deque
        self.time_deque = col.deque([], self.data_buffer_size)
        self.data_deque = col.deque([], self.data_buffer_size)
        self.return_fig.emit(time_deque, data_deque)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWindow = NumatoAdcGui()
    myWindow.show()
    app.exec_()

