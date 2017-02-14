#!/usr/bin/env python3

from PyQt5 import Qt, QtWidgets, uic
import sys
import time
import numpy as np
import numato_adc as nadc
import pyqtgraph as pg

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

        self.adc_plot_curve = self.adc_plot.plot()

        self._update_plot_timer = Qt.QTimer()
        self._update_plot_timer.timeout.connect(self.update)
        self.set_plot_update_time_s()
        self.update_time.editingFinished.connect(self.set_plot_update_time_s)
        self._timer_running = True
        self.start_stop.clicked.connect(self.toggle_update_plot_timer)

        # set plot defaults
        self.adc_plot.setLimits(yMin=0, yMax=5)

        # plotter and thread are none at the beginning
        self.plotter = Plotter()
        self.thread = Qt.QThread()

        self.send_fig.connect(self.plotter.replot)
        self.plotter.return_fig.connect(self.plot)
        self.plotter.moveToThread(self.thread)
        self.thread.start()

    def toggle_update_plot_timer(self):
        if self._timer_running:
            self._timer_running = False
            self._update_plot_timer.stop()
        else:
            self._timer_running = True
            self.set_plot_update_time_s()

    def set_plot_update_time_s(self):
        self._ticker = self.update_time.text()
        self._update_plot_timer.start(float(self._ticker)*1000.)

    def update(self):
        self.send_fig.emit(self._ticker)

    def plot(self, time, data):
        #self.adc_plot.line.set_data([np.arange(len(data)), data])
        self.adc_plot_curve.setData(time, data)
        #self.adc_plot.axes.set_xlim([0, len(data)])
        #self.adc_plot.axes.set_ylim([data.min(), data.max()])
        #self.adc_plot.draw()

class Plotter(Qt.QObject):
    return_fig = Qt.pyqtSignal(object, object)

    def __init__(self, data_buffer_size=50):
        Qt.QObject.__init__(self)
        self.start_time = time.time()
        self.time_buffer = np.zeros(data_buffer_size)
        self.data_buffer = np.zeros(data_buffer_size)

    def get_data(self):
        self.time_buffer = np.roll(self.time_buffer, -1)
        self.time_buffer[-1] = time.time() - self.start_time
        self.data_buffer = np.roll(self.data_buffer, -1)
        self.data_buffer[-1] = np.random.rand(1)
        return self.time_buffer, self.data_buffer

    @Qt.pyqtSlot(str)
    def replot(self, ticker):
        time, data = self.get_data()
        self.return_fig.emit(time, data)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWindow = NumatoAdcGui()
    myWindow.show()
    app.exec_()

