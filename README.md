# Backend Developer Test

This project is a template for a FastAPI application with a MySQL database, using Uvicorn as the ASGI server, Alembic for database migrations, and Redis for caching or background tasks.

## Prerequisites

Before you start, ensure you have the following installed:

- Python 3.8+
- MySQL database
- Redis server
- `pip` (Python package installer)

## Getting Started

Follow these steps to get the application up and running.

### 1. Clone the Repository

```bash
git clone https://github.com/pndiku/backend-developer-test.git
cd backend-developer-test
```

### 2. Set Up the Virtual Environment

Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configure the Environment Variables

Create a `.env` file in the project root directory and add the following environment variables:

```dotenv
DATABASE_URL=mysql+pymysql://backend:backend@localhost/backend_db
REDIS_URL=redis://localhost:6379/0
```

### 5. Set Up the Database

Ensure your MySQL server is running. Then, initialize the database using Alembic:

```bash
alembic upgrade head
```

### 6. Running the Application

Start the Uvicorn server to run your FastAPI application:

```bash
uvicorn app.main:app --reload
```

This command will start the server at `http://127.0.0.1:8000`.
## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
```
