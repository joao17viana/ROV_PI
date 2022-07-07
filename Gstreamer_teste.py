from threading import Thread
import cv2 as cv
import time
import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib

Gst.init()

main_loop = GLib.MainLoop()

main_loop_thread = Thread(target = main_loop.run)
main_loop_thread.start()

str_pipe =  "libcamerasrc ! decodebin ! videoconvert ! autovideosink"

pipeline = Gst.parse_launch(str_pipe)

pipeline.set_state(Gst.State.PLAYING)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

pipeline.set_state(Gst.State.NULL)
main_loop.quit()
main_loop_thread.join()

#class thread5(threading.Thread):
#    def __init__(self):
#        threading.Thread.__init__(self)
#        
#    def run(self):
#        # Main
#        while True:
#            print("Entrei na thread 5")
        # Vamos  definir variáveis e flags, nesta zona
        # Codigo da camera a partir daqui:
    