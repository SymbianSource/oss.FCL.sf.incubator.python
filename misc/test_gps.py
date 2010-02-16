"""

    Test case for causing uncatched exception in thread
    
    Mikko Ohtamaa <mikko@redinnovation.com>
    

"""
import e32
import thread
import time
import sys
import traceback
 
import positioning

done = False

        
debug_buf = []

def debug(msg):
    """ Output debug message from non-main thread """
    debug_buf.append(msg)
    
def cb(data):
    debug(str(data))

def go_thread():
    try:
        debug("GPS thread launching")
        positioning.set_requestors([{"type":"service","format":"application","data":"test_app"}])
    
        # interval: position update periof when gps is on (microseconds)
        # callback: callable to call when position update is available
        positioning.position(callback=cb, 
                             interval=5*1000*1000, 
                             satellites=1,
                             course=1,
                             partial = 1)
        
        death_point = time.time() + 10
        while time.time() < death_point :
            debug("GPS thread looping")
            e32.ao_sleep(1)
    except:
        info = sys.exc_info()
        debug(traceback.format_exception(*info))
                  
def run():
    global debug_buf
    
    death_point = time.time() +10
        
    test_thread = time.time()+2
    while time.time() < death_point :
        print "Pending"
        e32.ao_sleep(2)
                
        while len(debug_buf) > 0:
            msg = debug_buf[0]
            debug_buf = debug_buf[1:]
            if len(debug_buf) == 1:
                break
            print "Buffer %d Message: %s" % (len(debug_buf), msg)
            
        if time.time() > test_thread:
          thread.start_new_thread(go_thread, ())
                                
    # This row is never reached
    # The Python Interpreter shell is totally frozen
    # and it refuses to be terminated via Python task manager
    # -> phone must be restarted
    print "Done"
        
        
if __name__ == "__main__":
    run()