# Break & Patch CTF

Local CTF lab with vulnerable university portals and a dashboard for learning, solving challenges, and verifying patches.

| Service | URL | Purpose |
|---|---|---|
| CTF Dashboard | http://localhost:8000 | Learn content, challenges, Verify Patch |
| Broken Access Controls | http://localhost:5000 | Vulnerable portal (BAC) |
| Mishandling Exceptional Conditions | http://localhost:5001 | Vulnerable portal (MEC) |

Shared portal login for both apps:

- **username:** `ctfuser`
- **password:** `ctfpassword`

## Requirements

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop)

## Installation

1. Clone this repository and enter the project directory:

```bash
git clone <repo-url> break-patch-ctf
cd break-patch-ctf
```

2. Build and start all services:

```bash
docker compose up --build
```

3. Open the dashboard:

- http://localhost:8000

Leave the terminal running. To stop the lab:

```bash
docker compose down
```

### Optional: run in the background

```bash
docker compose up --build -d
docker compose logs -f
docker compose down
```

## How to use

1. Open the dashboard at http://localhost:8000.
2. Pick a module from the sidebar (Broken Access Controls or Mishandling Exceptional Conditions).
3. Read the Learn tab, then work through each challenge against the live portal.
4. Edit the vulnerable code under each app’s `challenge-files/` folder:
   - `broken-access-controls/challenge-files/`
   - `mishandling-exceptional-conditions/challenge-files/`
5. Because the apps run with `--reload`, code changes apply automatically after save.
6. Click **Verify Patch** on a challenge in the dashboard when you think your fix is correct.

## Troubleshooting

- If ports `5000`, `5001`, or `8000` are already in use, stop the conflicting process or change the host ports in `docker-compose.yml`.
- If Verify Patch cannot reach an app, confirm all three containers are up with `docker compose ps`.
- To reset a portal database from inside the app UI, use the reset control where available (MEC: Introduce Yourself page), or call `/api/reset-database` while logged in.
