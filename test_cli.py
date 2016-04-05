"""
Unit tests for the CLI.
"""
import logging
import unittest
import time

try:
    import queue
except ImportError:
    import Queue as queue

from cli import CLI


log = logging.getLogger(__name__)


class MockStdInOut(object):
    """ Mock version of stdin or stdout. """

    def __init__(self):
        """ Initialize the mock object. """
        self.received_data = []
        self.to_send_data = []

    def readline(self):
        """ Block until there is some data to return, then return it. """
        while self.to_send_data == []:
            pass

        return self.to_send_data.pop(0)

    def write(self, written_str):
        """ Store the written string for retrieval later. """
        self.received_data.append(written_str)

    def flush(self):
        """ Required to imitate a file-like object correctly. """
        pass


class TestCLI(unittest.TestCase):
    """ Basic CLI functionality test cases. """

    def setUp(self):
        """ Prepare mock stdin and stdout, and a CLI instance to test. """
        # Create stdin and stdout files for testing.
        self.test_stdinout = MockStdInOut()

        # Create queues to pass messages to and get messages from the CLI.
        self.to_cli_q = queue.Queue()
        self.from_cli_q = queue.Queue()

        # Create a test CLI with the test stdin and stdout.
        self.test_cli = CLI(self.to_cli_q, self.from_cli_q,
                            stdin=self.test_stdinout,
                            stdout=self.test_stdinout)
        self.test_cli.start()

    def tearDown(self):
        """ Just stop the test CLI instance. """
        self.test_cli.stop()

    def test_input_and_output(self):
        """ Test basic input and output of the CLI. """
        # Test that the CLI input works first.
        test_input = "This is some test input"
        self.test_stdinout.to_send_data.append(test_input + '\n')
        self.assertEqual(self.from_cli_q.get(timeout=0.5), test_input)

        # Now check the output. Pass a message to be written out.
        test_output = 'This is some test output'
        self.to_cli_q.put(test_output)
        # Wait for the output to be written.
        time.sleep(0.1)
        self.assertEqual(self.test_stdinout.received_data.pop(0),
                         test_output + '\n')

        # Check the CLI is still running happily.
        self.assertTrue(self.test_cli.running)

        # Finally, check there is no unread data in the files.
        self.assertEqual(self.test_stdinout.received_data, [])
        self.assertEqual(self.test_stdinout.to_send_data, [])

    def test_ending_session(self):
        """ Test the user can end the CLI instance cleanly. """
        # Simulate sending an EOF.
        self.test_stdinout.to_send_data.append('')
        self.assertEqual(self.from_cli_q.get(timeout=0.5), None)

        # This stops the reading thread, but nt the whole CLI - stop the rest.
        self.test_cli.stop()

        # Check the CLI is now stopped.
        self.assertFalse(self.test_cli.running)

        # Finally, check there is no unread data in the files.
        self.assertEqual(self.test_stdinout.received_data, [])
        self.assertEqual(self.test_stdinout.to_send_data, [])


def manual_test():
    """ Manual test for the CLI if needed. """
    to_cli_q = queue.Queue()
    from_cli_q = queue.Queue()
    cli = CLI(to_cli_q, from_cli_q)
    cli.start()
    log.info('CLI running state: %r', cli.running)

    time.sleep(10)

    log.info('CLI running state: %r', cli.running)
    cli.stop()

    try:
        while True:
            log.info('Got CLI input: %r', from_cli_q.get(timeout=0.1))
    except queue.Empty:
        pass


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:%(levelname) 5s:'
                               '%(lineno)-4d:%(message)s',
                        level=logging.INFO)
    unittest.main()
