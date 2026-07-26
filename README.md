# Break & Patch CTF

Learning Platform designed to teach the basics of A01 and A10 from OWASP Top 10 2025.


| Service                            | URL                                            | Purpose                                 |
| ---------------------------------- | ---------------------------------------------- | --------------------------------------- |
| CTF Dashboard                      | [http://localhost:8000](http://localhost:8000) | Learn content, challenges, Verify Patch |
| Broken Access Controls             | [http://localhost:5000](http://localhost:5000) | Vulnerable Web App                      |
| Mishandling Exceptional Conditions | [http://localhost:5001](http://localhost:5001) | Vulnerable Web App                      |


Shared portal login for both apps:

- **username:** `ctfuser`
- **password:** `ctfpassword`

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

## Installation

1. Clone this repository and enter the project directory:

```bash
git clone git@github.com:akaSaiba/break-patch-ctf.git <desired-folder>
cd <desired-folder>
```

2. Build and start all services:

```bash
docker compose up --build -d
```

3. Leave the terminal running. To stop all platforms:

```bash
docker compose down
```

## How to use

1. Open the dashboard at [http://localhost:8000](http://localhost:8000).
2. Read "Introduction" and familiarize yourself with the platform.
3. Let the learning begin! 
