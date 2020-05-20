import os
import tempfile

import pytest
from aops.app import create_testing_app


@pytest.fixture(scope="class", autouse=True)
def app():
    """Create and configure a new app instance for each test.

    Returns:
        Return a app instance for test purpose
    """
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    sqlite_db_path = 'sqlite:///{}'.format(db_path)

    # create the app with common test config
    app = create_testing_app({
        "SQLALCHEMY_DATABASE_URI": sqlite_db_path,
    })

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="class", autouse=True)
def client(app):
    """A test client for the app.

    Args:
        App instance
    Returns:
        client: Standard flask test client
    """
    return app.test_client()


@pytest.fixture(scope="class", autouse=True)
def runner(app):
    """A test runner for the app's Click commands.

    Args:
        App instance
    Returns:
        runner: Standard flask cli runner
    """
    return app.test_cli_runner()
