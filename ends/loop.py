# -*- coding: utf-8 -*-
__all__ = ['run', 'stop']

from threading import Event, Thread
import code
import time
import logging
import sys
from . import api


started = Event()
stopped = Event()


def stop():
    stopped.set()


def run(interactive=False):

    # Make sure the event loop is not already running
    if started.isSet():
        raise Exception('Event loop already initialized')

    # Create an active graph is there is none
    if not api.get_graph():
        api.new_graph('untitled')

    # Set up our console
    if interactive:
        import ends
        console = code.InteractiveConsole(locals=dict(globals(), **locals()))
        print('Starting interactive ends session...')
        if api.NODE_TYPES:
            print('The following functions are registered:')
            for name in api.NODE_TYPES:
                print('    ', name)


    try:

        exc = None
        started.set()

        while True:

            # Check if we've stopped
            if stopped.isSet():
                break

            # Get some input from user
            if interactive:
                try:
                    more_input = console.push(console.raw_input('>>> '))
                    while more_input:
                        more_input = console.push(console.raw_input('... '))
                except SystemExit as e:
                    raise
                except KeyboardInterrupt as e:
                    exc = e
                    print(e)
                    break
                except Exception as e:
                    exc = e
                    print(e)

            # Evaluate the active graph
            try:
                api.evaluate()
            except KeyboardInterrupt as e:
                exc = e
                print(e)
                break
            except Exception as e:
                if e != exc:
                    print(e)
                exc = e

    finally:

        started.clear()
        stopped.clear()
