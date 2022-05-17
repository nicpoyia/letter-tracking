# Letter Tracking System using a Postal Service API

### By Nicolas Poyiadjis
https://www.linkedin.com/in/nicpoyia/

## How to run and test

### Environment Setup
- Install python 3.7 & pipenv
- `pipenv install` to install project's requirements
- Before running the API, export the environment variable called LA_POSTE_API_KEY, which is the authorization key for La Poste API `export LA_POSTE_API_KEY=LA_POSTE_API_KEY_HERE`
- Working tracking IDs are already stored in the sample SQLite database, therefore by retrieving statuses of all letters should return results. 
- Execute command `flask run` to run the application's API
- You can use postman_demo.json for a demo of the API

### Automated Tests
- Execute command `pipenv install -d` to install all dependencies required for development environment
- Execute command `python -m pytest tests/` to run all automated tests

There have been implemented 3 types of automated tests:
- Unit tests, in which the model and data classes are being tested independently (the smallest units - the lowest layer)
- Module tests (or service tests, or integration tests), in which the service containing the logic is tested by integrating a mock implementation of each external dependency, which in this case is La Poste API
- End-to-end tests, in which the application is tested as a whole by running its HTTP API using mock dependencies

In order to run the tests independently of production infrastructure, an independent SQLite database is generated on demand for testing purposes, i.e. before running the tests it is automatically created (if not yet) and the schema is initialized according to the application's migrations

### Database Setup
The database is already initialized with the updated schema and sample data to allow observing the application in action

The command `flask db upgrade` is used to initialize the configured database with the appropriate schema (no data will be lost if it is already initialized).
