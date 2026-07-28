# DoualaTrotter – Travel Assistant (Douala Edition)

DoualaTrotter is a **monolithic Flask application** that serves as the starting point for a semester-long capstone project.
It is an adaptation of the original GlobeTrotter project, focused on the city of **Douala, Cameroon** — helping users discover destinations, activities, and local transport options (taxi, moto-taxi, VTC, family vans).

Students build the monolith first, then refactor it into microservices, and finally deploy it to the cloud with resilience patterns using Docker, Kubernetes, and cloud-native tooling.

---

## Project Structure

```
.
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── models.py           # Data models and JSON file I/O
│   ├── auth.py             # Registration, login, JWT handling
│   ├── destinations.py     # Destination search endpoint (Douala attractions)
│   ├── activities.py       # Activity search endpoint (things to do in Douala)
│   ├── transport.py        # Transport search + reservation endpoint (taxi, moto, VTC, van)
│   ├── recommendations.py  # Personalised recommendations across all 3 categories
│   ├── itineraries.py      # Create / list itineraries
│   └── main.py             # App entry point
├── data/
│   ├── destinations.json   # Static catalogue of Douala attractions (seed data)
│   ├── activities.json     # Static catalogue of activities in Douala (seed data)
│   ├── transport.json      # Static catalogue of transport options (seed data)
│   ├── users.json          # Created at runtime
│   ├── itineraries.json    # Created at runtime
│   └── reservations.json   # Created at runtime
├── tests/                  # Unit tests (pytest)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_destinations.py
│   ├── test_activities.py
│   └── test_transport.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## REST API

| Method | Endpoint                    | Auth required | Description                                       |
|--------|------------------------------|----------------|---------------------------------------------------|
| POST   | `/register`                 | No             | Register a new user                                |
| POST   | `/login`                    | No             | Authenticate and receive a JWT token               |
| GET    | `/destinations`             | No             | Search the Douala destination catalogue            |
| GET    | `/activities`               | No             | Search the Douala activity catalogue                |
| GET    | `/transport`                | No             | Search available transport options                  |
| POST   | `/transport/reserve`        | Yes (JWT)      | Reserve a transport option                          |
| GET    | `/transport/reservations`   | Yes (JWT)      | List the logged-in user's transport reservations    |
| GET    | `/recommendations`          | Yes (JWT)      | Get personalised recommendations (destinations, activities, transport) |
| POST   | `/itineraries`              | Yes (JWT)      | Create a new itinerary                              |
| GET    | `/itineraries`              | Yes (JWT)      | List all itineraries for the logged-in user         |

Protected routes expect the header:
`Authorization: Bearer <your-token>`

Free-text search (`q`), `tag`, and `quartier` filters on `/destinations` and `/activities` are **accent-insensitive** (e.g. `marche` matches `Marché`).

### Example requests

```bash
# Register
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t", "preferences": ["culture", "famille"]}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t"}'
# Save the returned token: TOKEN=<value from .token field>

# Search destinations
curl "http://localhost:5000/destinations?quartier=Akwa&tag=culture"

# Search activities
curl "http://localhost:5000/activities?tag=famille"

# Search transport (e.g. family vans only)
curl "http://localhost:5000/transport?type=van_familial&disponible=true"

# Reserve a transport option
curl -X POST http://localhost:5000/transport/reserve \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"transport_id": "taxi-011", "depart": "Bonanjo", "destination": "Aeroport de Douala"}'

# List my transport reservations
curl http://localhost:5000/transport/reservations \
  -H "Authorization: Bearer $TOKEN"

# Personalised recommendations (destinations + activities + transport)
curl http://localhost:5000/recommendations \
  -H "Authorization: Bearer $TOKEN"

# Create an itinerary
curl -X POST http://localhost:5000/itineraries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Weekend a Douala", "destinations": ["Marche Central", "Doual art"], "start_date": "2026-08-01", "end_date": "2026-08-03"}'

# List itineraries
curl http://localhost:5000/itineraries \
  -H "Authorization: Bearer $TOKEN"
```

---

## Running Locally

### Prerequisites
- Python 3.9+
- pip

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python -m app.main
```

> **Note:** run the server with `python -m app.main` (not `python app/main.py`), so Python
> resolves the `app` package correctly from the project root.

The API will be available at `http://localhost:5000`.

---

## Running Tests

This project uses [pytest](https://docs.pytest.org/). Tests run against an isolated
temporary data directory, so they never touch your real `data/*.json` files.

```bash
python -m pytest tests/ -v
```

---

## Running with Docker

```bash
# Build and start
docker-compose up --build

# Stop
docker-compose down
```

The `data/` directory is mounted into the container, so JSON files persist between runs.

---

## Data Storage

All data is persisted in plain JSON files inside the `data/` directory:

| File                      | Purpose                                              |
|---------------------------|-------------------------------------------------------|
| `data/destinations.json`  | Static catalogue of Douala attractions (seed data)     |
| `data/activities.json`    | Static catalogue of activities in Douala (seed data)   |
| `data/transport.json`     | Static catalogue of transport options (seed data)      |
| `data/users.json`         | Registered users (created at runtime)                 |
| `data/itineraries.json`   | User itineraries (created at runtime)                  |
| `data/reservations.json`  | Transport reservations (created at runtime)            |

> **Note:** `data/*.json` are excluded from version control via `.gitignore`. Seed files
> (`destinations.json`, `activities.json`, `transport.json`) are force-added with
> `git add -f` so they stay tracked despite the ignore rule.

---

## Configuration

| Environment Variable | Default                              | Description           |
|-----------------------|---------------------------------------|-------------------------|
| `SECRET_KEY`          | `globetrotter-secret-change-in-prod`  | JWT signing key – **must be overridden in production** |
| `FLASK_DEBUG`         | `0`                                    | Set to `1` to enable Flask debug mode (development only) |
| `PORT`                | `5000`                                 | Port the app listens on |

> **Important:** Always set `SECRET_KEY` to a long, random value in production (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`).
