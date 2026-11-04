# Fredagsbarens event-system

Et event-system med Flask API og Streamlit-frontend.
Frontenden kommunikerer med API’en via HTTP med httpx.

## Forudsætninger

- Docker med Docker Compose til containerkørsel.
- Python 3.12 og uv til lokal udvikling uden Docker.

## Start med Docker

Kør fra projektets rod:

```bash
docker compose up --build
```

Åbn:

- Frontend: http://localhost:8501
- API: http://localhost:5001/events

API’en kan testes i Postman på http://localhost:5001.

Stop systemet med Ctrl+C. Fjern derefter projektets containere
og netværk med:

```bash
docker compose down
```

## Start lokalt uden Docker

Installer afhængigheder:

```bash
uv sync --frozen
```

Start API’en i én terminal:

```bash
uv run api.py
```

Start frontenden i en anden terminal:

```bash
uv run streamlit run app.py
```

Stop Docker-containerne før lokal kørsel, så portene er ledige.

## Brug af systemet

1. Vælg et event.
2. Skriv dit navn i feltet under Tilmelding.
3. Klik Tilmeld.
4. Klik Afmeld ud for dit navn for at fjerne tilmeldingen.

Nye events oprettes i formularen nederst på siden.

## API-endpoints

| Metode | Sti | Formål |
|---|---|---|
| GET | /events | Hent alle events |
| GET | /events/<id> | Hent ét event |
| POST | /events | Opret et event |
| POST | /events/<id>/signups | Tilmeld en person |
| DELETE | /events/<id>/signups/<name> | Afmeld en person |
| DELETE | /events/<id> | Slet et event |

API-dokumentationen findes i swagger.json og kan åbnes i Swagger Editor.

## Konfiguration

Frontenden læser API-adressen fra miljøvariablen API_URL.

- Lokalt er standardadressen http://127.0.0.1:5001.
- I Docker Compose sættes adressen til http://api:5001.

## Datalagring

Events og tilmeldinger gemmes i API-processens hukommelse.
Ved genstart af API’en nulstilles data til projektets startdata.

Navnet gemmes i Streamlits session state og bevares mellem
genkørsler i samme session.

## Afvigelse fra opgavebeskrivelsen

Navnefeltet er placeret under Tilmelding i hovedvisningen
i stedet for i sidebaren.