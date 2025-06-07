# Singapore Address Validator

[👉 Visit the Web App](http://ec2-3-106-116-1.ap-southeast-2.compute.amazonaws.com:8000/)

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
3. CI/CD pipeline using GitHub Actions for linting, testing, and building the Python package
4. Containerization using Docker
5. Cloud deployment on AWS EC2
6. OneMap API integration for address validation
7. Web scraping StreetDirectory.com to infer property types
8. Custom heuristic address parsing to normalize messy user input (e.g., extracting postal code, unit number, street name)


Planned improvements:
1. CI/CD pipeline for automated deployment to AWS EC2 via GitHub Actions
2. User upload interface to support batch address validation via spreadsheet (Excel/CSV)
3. Heuristic and LLM to intelligently guess column and row formats in uploaded Excel/CSV files
4. Add logging and monitoring
5. Search result caching with PostgreSQL database
6. User login and customization

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
uvicorn src.app.main:app --reload
```
