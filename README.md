# AI-Powered User Profile Management & Semantic Matching API

A Django REST Framework backend for managing authenticated user profiles, generating AI-powered professional summaries with Google Gemini, creating 384-dimensional text embeddings using Sentence Transformers, and finding semantically related profiles with PostgreSQL + pgvector.


## Features

- **JWT authentication: Registration, login, refresh, logout, and current-user endpoint.
- **Profile management: Create, view, update, and delete user profiles; one profile per user.
- **AI summary generation: Generate a concise professional summary from profile fields with Google Gemini.
- **Local embeddings: Convert profile text and search queries into 384-dimensional vectors using `sentence-transformers/all-MiniLM-L6-v2`.
- **Semantic search: Rank discoverable user profiles by cosine similarity using PostgreSQL's `pgvector` extension.
- **Profile-to-profile matching:** Find profiles semantically similar to a selected profile.
- **Search history: Persist search requests, ranked matches, and similarity scores.
- **Privacy and ownership:** JWT-protected endpoints, owner-only profile editing, and opt-in discoverability.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Authentication | Django built-in User + SimpleJWT |
| Relational and vector database | PostgreSQL with `pgvector` |
| Embedding model | Sentence Transformers: `all-MiniLM-L6-v2` (384 dimensions) |
| AI-generated summaries | Google Gemini (`google-genai`) |
| API testing | Postman |
| Database inspection | DBeaver or pgAdmin |


## Database schema and relationships

| Table | Purpose |
|---|---|
| `auth_user` | Original Django users and password hashes; **unchanged** |
| `accounts_account` | Additional account details (`user_id`, `display_name`, `phone`, timestamps) |
| `profiles_profile` | Profile fields, summary, embedding, visibility, timestamps |
| `matching_matchingquery` | Search owner, search type, raw query or source profile, limit, threshold |
| `matching_matchresult` | Matched profile, ranking, similarity score, and corresponding search |


## Local setup (Windows)

### 1. Requirements

- Python compatible with the project's installed Django and ML packages (Python 3.12 or 3.13 recommended for this codebase).
- PostgreSQL running locally (the project has been used with PostgreSQL 17 on Windows).
- `pgvector` installed on the PostgreSQL server, not only the Python `pgvector` package.
- Valid Gemini API key for the summary endpoint.
- Internet access when downloading the embedding model for the first time.

### 2. Install Python dependencies

```powershell
cd AI_Profile_Matcher
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the existing `venv` is working, activate it rather than creating a second one. `requirements.txt` should include Django, DRF, SimpleJWT, `psycopg[binary]`, `pgvector`, `sentence-transformers`, `python-dotenv`, and `google-genai`.

### 3. Configure `.env`

Create or update the `.env` file in the folder containing `manage.py`:

```dotenv
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=ai_profile_matcher
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
DB_HOST=127.0.0.1
DB_PORT=5432

GEMINI_API_KEY=your_gemini_api_key
GEMINI_SUMMARY_MODEL=your_available_gemini_model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Use the actual PostgreSQL credentials and a Gemini model available to your API key. Never commit `.env`, passwords, or API keys.


### 4. Enable pgvector

In DBeaver, connect to the same database specified by `DB_NAME` and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

If PostgreSQL reports `vector.control` not found, install the pgvector extension files into the PostgreSQL server installation first. The `pip install pgvector` command alone does not install the server extension.

### 5. Check and apply migrations

The existing `profiles` migration may already be applied; the safe-table patch adds initial `accounts` and `matching` migrations.

```powershell
python manage.py check
python manage.py showmigrations accounts matching profiles
python manage.py makemigrations --check --dry-run
python manage.py migrate accounts
python manage.py migrate matching
python manage.py migrate
```


### 6. Run the server

```powershell
python manage.py runserver
```

- Base URL: `http://127.0.0.1:8000`
- Health check: `GET http://127.0.0.1:8000/health/` → `{"status": "ok"}`

The health check only proves Django is responding; it does not prove that Gemini, the embedding model, or PostgreSQL vector queries work.

## API reference

Use `Content-Type: application/json`. Except registration, login, and token refresh, supply `Authorization: Bearer <access_token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/register/` | Register user |
| `POST` | `/api/auth/login/` | Obtain JWT access and refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Refresh access token |
| `POST` | `/api/auth/logout/` | Blacklist owned refresh token |
| `GET` | `/api/auth/me/` | Read logged-in user |
| `GET` | `/api/profiles/` | List public profiles and the caller's own profile |
| `POST` | `/api/profiles/` | Create own profile |
| `GET` | `/api/profiles/me/` | Read own profile |
| `PATCH`, `PUT` | `/api/profiles/me/` | Update own profile |
| `DELETE` | `/api/profiles/me/` | Delete own profile |
| `GET` | `/api/profiles/<id>/` | Read a public profile or caller's own |
| `POST` | `/api/profiles/me/summary/` | Generate a Gemini profile summary |
| `POST` | `/api/profiles/me/embedding/refresh/` | Rebuild own embedding |
| `POST` | `/api/matching/search/` | Semantic query-to-profile search |
| `GET` | `/api/matching/profiles/<id>/similar/` | Profile-to-profile similarity search |
| `GET` | `/api/matching/history/` | List the caller's saved search history |
| `GET` | `/api/matching/history/<id>/` | Get one saved search with results |
| `GET` | `/health/` | Basic health check |


## End-to-end Postman walkthrough

### Step 1: Register two users

**POST** `/api/auth/register/`

```json
{
  "username": "rahul",
  "email": "rahul@gmail.com",
  "password": "SecurePass@12345",
  "password_confirm": "SecurePass@12345",
  "first_name": "Rahul",
  "last_name": "Sharma"
}
```

Register a second user (`priya`, `priya@gmail.com`) with a unique username and email. Registration should create an authentication user and return JWT tokens in the supported registration implementation. A user can have **one** profile.

### Step 2: Log in and set Bearer token

**POST** `/api/auth/login/`

```json
{
  "username": "rahul",
  "password": "SecurePass@12345"
}
```

Copy the returned `access` token into Postman → **Authorization** → **Bearer Token** for subsequent requests.

### Step 3: Create a profile

**POST** `/api/profiles/`

```json
{
  "full_name": "Rahul Sharma",
  "headline": "Python Backend Developer",
  "bio": "I develop scalable backend applications with Django and REST APIs.",
  "occupation": "Software Engineer",
  "education": "B.Tech Computer Science",
  "location": "Bangalore",
  "skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "interests": ["Artificial Intelligence", "Backend Development"],
  "experience_years": 3,
  "is_discoverable": true
}
```

Create Priya's profile using Priya's token, with relevant but different skills and `experience_years: 5`. A successful profile creation should result in `embedding_status: "ready"` if local embedding generation succeeds; on failure, the status may be `failed`.

### Step 4: Generate an AI summary

**POST** `/api/profiles/me/summary/` — no JSON body.

The backend sends selected profile fields to **Gemini** and saves the returned summary in `profiles_profile.ai_summary`. It then attempts to regenerate the profile embedding so the summary can contribute to semantic matching.

A missing or failing Gemini API call typically returns HTTP **503**, with an error `detail`. Check the API key, model availability, network connection, and Django logs. The embedding model and Gemini summary model are separate services.

### Step 5: Check or regenerate embeddings

**POST** `/api/profiles/me/embedding/refresh/` — no JSON body.

Embeddings are generated locally with the Sentence Transformers model. Each successful vector has **384 dimensions**, and the profile must be discoverable and `embedding_status: "ready"` to appear in public matching results.

### Step 6: Search profiles semantically

**POST** `/api/matching/search/`

```json
{
  "query": "Looking for an Artificial Engineer experience three years having name Rahul",
  "limit": 2,
  "min_score": 0.0
}
```

Example response **shape** (scores are examples, not guaranteed):

```json
{
  "search_id": 1,
  "query": "Looking for an Artificial Engineer experience three years",
  "count": 2,
  "matches": [
    {
      "profile": {"id": 1, "full_name": "Rahul Sharma"},
      "similarity_score": 0.5653
    },
    {
      "profile": {"id": 2, "full_name": "Priya Singh"},
      "similarity_score": 0.4604
    }
  ]
}
```

Real responses contain additional profile fields. Results are ordered from highest to lowest semantic similarity. Valid parameters in this implementation: `limit` 1–50 and `min_score` 0.0–1.0.

### Step 7: Find profiles similar to one profile

**GET** `/api/matching/profiles/1/similar/?limit=5&min_score=0.0`

Replace `1` with the desired source profile ID. Only discoverable profiles with ready vectors are eligible as results; the source profile is excluded. A private source profile can only be used by its owner.

### Step 8: View matching history

**GET** `/api/matching/history/` and **GET** `/api/matching/history/1/` (use a real `search_id`). Only the authenticated user can access their own history. A successful search stores the query even when there are zero matches; result rows are created only for matched profiles.

```


The implementation uses:

```text
query_embedding = SentenceTransformer(query)
profile_embedding = stored profile vector
cosine_distance = pgvector CosineDistance(profile_embedding, query_embedding)
similarity_score = 1 - cosine_distance
```

The API clamps displayed scores to 0–1. Do not increase scores artificially. If exact name or experience matching is required, add explicit structured filters or hybrid ranking; those filters are not implemented by the current free-text matching endpoint.

## Verify the database in DBeaver

Use the same database selected by Django's `.env` settings.

### List relevant tables

```sql
SELECT schemaname, tablename
FROM pg_catalog.pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'auth_user', 'accounts_account', 'profiles_profile',
    'matching_matchingquery', 'matching_matchresult'
  )
ORDER BY tablename;
```

### Check Account extension records

```sql
SELECT a.id, a.user_id, u.username, a.display_name, a.phone
FROM accounts_account AS a
JOIN auth_user AS u ON u.id = a.user_id
ORDER BY a.id;
```

### Check profile embeddings

```sql
SELECT
    id, full_name, experience_years, embedding_status,
    embedding_model, vector_dims(embedding) AS embedding_dimensions
FROM profiles_profile
ORDER BY id;
```

Successful embeddings should show `ready` and `384` dimensions. A profile created before the embedding service was working may have a `NULL` vector and need a refresh.

### Check search history and match results

```sql
SELECT id, user_id, search_type, query_text, requested_limit, min_score, created_at
FROM matching_matchingquery
ORDER BY id DESC;

SELECT search_id, matched_profile_id, rank, similarity_score
FROM matching_matchresult
ORDER BY search_id DESC, rank;
```

If the tables exist but contain no rows, that usually means the relevant action has not been performed yet. A table's existence and its data population are separate checks.

## Security notes

- Only the profile owner can update or delete their profile.
- A private profile (`is_discoverable: false`) should not appear in other users' semantic search results.
- Embedding vectors are stored in PostgreSQL but are not included in normal profile API responses.
- Profile summary requests send selected profile data to Gemini; inform users that this is an external AI operation.
- Search-history tables store the query text and results. Restrict access and set a retention policy before production use.


## Testing and troubleshooting

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations accounts matching profiles
python manage.py test
```


## Assignment coverage

| Requirement | Implementation |
|---|---|
| **A. Authentication and authorization** | JWT auth, passwords stored as hashes, protected routes, permission checks |
| **B. User profile management** | Create/read/update/delete profile and visibility settings |
| **C. AI-powered profile summary** | Gemini-powered summary generation and persistence |
| **D. Vector database integration** | PostgreSQL + pgvector, 384-dimensional vectors, HNSW cosine index |
| **E. Semantic profile matching** | Query/profile embeddings, cosine ranking, query-to-profile and profile-to-profile matches, optional saved history |


