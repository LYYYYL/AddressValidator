# Singapore Address Validator

[👉 Visit the Web App](https://54.253.236.7/)

This project provides an address validation service tailored for small business owners in Singapore.
It helps detect invalid or incomplete addresses, which are common causes of failed deliveries, redeliveries, and increased customer support.

What it does:
1. Validates Singapore postal codes
2. Infers property type and checks for missing unit numbers
3. Verify block number and street name against postal code

What it doesn't do:
1. Validate the correctness of specific unit numbers (requires the paid SingPost SGLocate service)

## Inner workings
Stack overview:
1. Python (Object-Oriented Programming) with design patterns and Test-Driven Development (TDD)
2. FastAPI backend with NiceGUI frontend
3. CI/CD pipeline using GitHub Actions for linting, testing, building the Python package, and auto-deploying to AWS EC2
4. Containerization using Docker
5. Cloud deployment on AWS EC2
6. OneMap API integration for address validation
7. Web scraping StreetDirectory.com to infer property types
8. Custom heuristic address parsing to normalize messy user input (e.g., extracting postal code, unit number, street name)


Planned improvements:
1. User upload interface to support batch address validation via spreadsheet (Excel/CSV)
2. Heuristic and LLM to intelligently guess column and row formats in uploaded Excel/CSV files
3. Add logging and monitoring
4. Search result caching with PostgreSQL database
5. User login and customization

## Development quick start on Ubuntu Linux/WSL2 for Windows

```bash
# clone the repo
git clone https://github.com/LYYYYL/AddressValidator.git

# Enter root directory
cd AddressValidator

# install the dev dependencies
make install

# run the tests
make test

# Run the FastAPI app with auto-reload for development
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
# Open your webbrowser and access http://localhost:8000

```
