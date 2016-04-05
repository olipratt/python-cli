# Python CLI

A simple Python CLI to allow interaction with a user at the command prompt.

## Prerequisites

Works with Python 2 or 3. No non-default packages.

## Usage

Example usage:

    from queue import Queue

    # Create queues for communication, and create an instance of the CLI.
    to_user_queue = Queue()
    from_user_q = Queue()

    my_cli = CLI(to_user_queue, from_user_q)

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

See docstrings for more detailed info.

## Tests

Just run `python test_cli.py` to run the tests.
