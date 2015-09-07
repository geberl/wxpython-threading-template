# -*- coding: utf-8 -*-
__author__ = 'guenther@eberl.se'

# Import program components / modules from python standard library / non-standard modules.
import gui
import wx

import logging
import logging.config
import os
import sys
import platform
import datetime
import threading
import time


# Logging config on sub-module level.
logger = logging.getLogger(__name__)


class MainFrame(gui.MainFrame):
    def __init__(self, parent):
        gui.MainFrame.__init__(self, parent)
        logger.debug('Running __init__ ...')

        # Bind the "on close" event.
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Remember if user clicked on close while the thread was running.
        self.user_clicked_close = False

        # Bind the monitoring buttons.
        self.ButtonStartMonitoring.Bind(wx.EVT_BUTTON, self.start_monitoring)
        self.ButtonStopMonitoring.Bind(wx.EVT_BUTTON, self.stop_monitoring)

        # Enable/Disable monitoring buttons correctly.
        self.ButtonStartMonitoring.Enable(True)
        self.ButtonStopMonitoring.Enable(False)
        self.DateTimeText.SetLabelText(u'Last action: -')

        # Determine if program is running compiled to *.exe/*.app or from Python interpreter.
        if hasattr(sys, 'frozen'):
            self.application_path = os.path.dirname(sys.executable)
        else:
            self.application_path = os.path.dirname(__file__)

        # Set the application icon, unsupported on Mac OS X.
        if platform.system() != 'Darwin':
            ico = wx.Icon(self.application_path + os.sep + 'icon.ico', wx.BITMAP_TYPE_ICO)
            self.SetIcon(ico)

        # Refresh settings.
        self.continue_time_refresh = False
        self.refresh_gui_seconds = 0.25
        self.action_seconds = 10

        # Set the options of the gauge element.
        self.gauge_max_value = 100
        self.Gauge.SetRange(self.gauge_max_value)

    def start_monitoring(self, event):
        logger.debug('Starting to do_monitoring thread/GUI (event Id %i).' % event.GetId())

        # Enable/Disable monitoring buttons correctly.
        self.ButtonStartMonitoring.Enable(False)
        self.ButtonStopMonitoring.Enable(True)

        # Start by doing what happens inside the loop otherwise, since the loop starts with a pause.
        self.refresh_timer()
        self.take_action()

        # Setup loop exit variable and start thread.
        self.continue_time_refresh = True
        thread_0 = threading.Thread(target=self.do_monitoring, name='refresh time', args=())
        thread_0.daemon = False
        thread_0.start()

        # Bind the window close event to the stop monitoring function.
        self.Bind(wx.EVT_CLOSE, self.stop_monitoring)

    def do_monitoring(self):
        gauge_current_value = self.gauge_max_value
        while self.continue_time_refresh is True:
            try:
                # Delay next refresh some seconds.
                time.sleep(self.refresh_gui_seconds)

                # Take action always when the gauge hits 0.
                if gauge_current_value == 0:
                    # Refresh timer.
                    self.refresh_timer()

                    # Actually do the thing that should happen periodically (take screenshot, analyse file, etc.).
                    self.take_action()

                # Set gauge to refresh value.
                if gauge_current_value <= 0:
                    gauge_current_value = 100
                else:
                    gauge_current_value -= self.gauge_max_value / (self.action_seconds / self.refresh_gui_seconds)
                self.Gauge.SetValue(gauge_current_value)

            except Exception as exc:
                logger.debug(exc)
                time.sleep(self.refresh_gui_seconds)

        # Run loop exit function only after loop finishes its last run.
        wx.CallAfter(self.exit_loop)

    def stop_monitoring(self, event):
        logger.debug('Stopped monitoring thread/GUI (event Id %i).' % event.GetId())

        # Disable all buttons. Only when the loop actually exits the start button is enabled again.
        self.ButtonStartMonitoring.Enable(False)
        self.ButtonStopMonitoring.Enable(False)

        # Exit loop in thread on next run. This is the next possibility for a clean exit.
        self.continue_time_refresh = False

        # Check and remember if the user clicked the window close button.
        if event.ClassName == 'wxCloseEvent':
            self.user_clicked_close = True

    def refresh_timer(self):
        # Refresh the line in the GUI where the last run time/date of take_action() is displayed.
        datetime_now = datetime.datetime.now()
        date_string_for_gui = datetime_now.strftime('%Y-%m-%d %H:%M:%S')
        self.DateTimeText.SetLabelText(u'Last action: ' + date_string_for_gui)
        self.MainPanel.Layout()  # needed for correct centered alignment when the date/time string length changes.

    @staticmethod
    def take_action():
        logger.info('Taking action....')  # Placeholder for the real thing.

    def exit_loop(self):
        # Enable/Disable monitoring buttons correctly.
        self.ButtonStartMonitoring.Enable(True)
        self.ButtonStopMonitoring.Enable(False)

        # Reset text and gauge.
        self.Gauge.SetValue(0)
        self.MainPanel.Layout()

        # Rebind window close event to the function that actually closes the window.
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Now close the window if user clicked on close button.
        if self.user_clicked_close:
            self.on_close(wx.CloseEvent)

    def on_close(self, event=None):
        if event:
            logger.debug('Closing GUI while thread was NOT running (event Id %i).')
        else:
            logger.debug('Closing GUI while thread was running.')
        self.Destroy()
