"""
A CLI for input/output of messages between a user and a Python program.

Create an instance of the CLIInput class, providing two queues to pass messages
to the user and receive messages from the user respectively.

Example usage:

    from queue import Queue

    to_user_queue = Queue()
    from_user_q = Queue()

    my_cli = CLIInput(to_user_queue, from_user_q)

    # Start the CLI, which means it will be running.
    my_cli.start()
    assert my_cli.running

    # Say hello to the user.
    to_user_queue.put("Hello user")

    # Wait for a response from the user.
    response = from_user_q.get()

    # Stop the CLI.
    my_cli.stop()
    assert not my_cli.running
"""

import queue
import threading
import sys
import logging


log = logging.getLogger(__name__)


# How long to block waiting for a message on a queue before checking that we're
# still running - in seconds.
# This stops us blocking forever. A short timeout means stopping the CLI is
# quicker, but at the cost of higher CPU usage while it's running.
OUTPUT_QUEUE_BLOCK_TIME = 0.25


class CLIInput(object):
    """ An object that provides a command line interface to read in commands
        from users and write responses back out. """

    def __init__(self, to_user_q, from_user_q,
                 stdin=sys.stdin, stdout=sys.stdout):
        """ Initialise a new CLI Input. """
        log.debug('Initialising a new CLI instance')

        # Store the stdin and stdout to read from/write to.
        self._stdin = stdin
        self._stdout = stdout

        # Queues to read messages from to output to the user, or put messages
        # from the user on to.
        self._to_user_queue = to_user_q
        self._from_user_queue = from_user_q

        # Flag indicating if the CLI is running.
        self._running = False

        # Threads that handle the input and output.
        self._to_user_thread = None
        self._from_user_thread = None

    def start(self):
        """ Starts the CLI.

        It will run until it gets an EOF at the prompt, or is stopped by a call
        to stop.
        """
        log.debug("Starting CLI")
        if not self._running:
            log.debug("CLI is not running")
            self._running = True
            self._start_threads()

        log.debug('CLI is started')

    def stop(self):
        """ Stops the CLI. """
        log.debug("Stopping CLI")
        if self._running:
            log.debug("CLI is running - stopping")
            self._running = False
            self._join_threads()

        log.debug("CLI is stopped")

    @property
    def running(self):
        """ Returns whether the CLI has been started. """
        log.debug('Returning if CLI is running: %s', self._running)
        return self._running

    def _start_threads(self):
        """ Start the threads that get from/put on the input/output queues. """
        log.debug("Starting CLI threads")
        self._to_user_thread = \
            threading.Thread(target=self._output_commands_to_prompt)
        self._to_user_thread.daemon = True

        self._from_user_thread = \
            threading.Thread(target=self._read_commands_from_prompt)
        self._from_user_thread.daemon = True

        self._to_user_thread.start()
        self._from_user_thread.start()

    def _join_threads(self):
        """ Wait briefly for threads to exit. Ignore failures.

        In particular, there's no way to stop the reading thread if it's
        blocking reading input, so just leave it running and it will exit if
        anything is input, or the whole program exits. Unfortunately, there's
        nothing we can do about that.
        """
        try:
            self._to_user_thread.join(2 * OUTPUT_QUEUE_BLOCK_TIME)
        except RuntimeError:
            log.exception("To user thread didn't exit - ignoring")
        try:
            self._from_user_thread.join(2 * OUTPUT_QUEUE_BLOCK_TIME)
        except RuntimeError:
            log.exception("From user thread didn't exit - ignoring")

    def _read_commands_from_prompt(self):
        """ Loops continuously, getting input from stdin and storing the
            strings provided in an internal queue.
            Stops running if we get an EOF, and puts None onto the queue.
        """
        log.debug('Starting command input loop')
        while self._running:
            # This read will block indefinitely and there's no nice way to
            # periodically drop out that I've found. This might cause problems
            # if the CLI is started, stopped, and restarted...
            raw_command = self._stdin.readline()

            if raw_command == '':
                log.debug("Got EOF - exiting")
                self._from_user_queue.put(None)
                break

            command = raw_command.rstrip('\n')
            log.debug('Got command from prompt: %s', command)
            self._from_user_queue.put(command)

        log.debug("Stopping input reading loop")

    def _output_commands_to_prompt(self):
        """ Loops continuously, writing out responses from the internal output
            queue to the prompt.
        """
        log.debug('Starting command output loop')
        while self._running:
            try:
                # Block waiting for a message to output, but regularly drop
                # out to make sure we're still running.
                response = self._to_user_queue.get(OUTPUT_QUEUE_BLOCK_TIME)
            except queue.Empty:
                pass
            else:
                log.debug('Writing out response: %s', response)
                self._stdout.write('{}\n'.format(response))
                self._stdout.flush()

        log.debug("Stopping output writing loop")
