import os
from urllib.parse import quote
import httpx
import streamlit as st


# API-adressen kan erstattes via en miljøvariabel ved kørsel i Docker.
API_URL = os.environ.get("API_URL", "http://127.0.0.1:5001").rstrip("/")


def api_request(method, path, json=None):
    """Sender en HTTP-request og viser forståelige fejl i brugerfladen."""
    try:
        response = httpx.request(
            method,
            f"{API_URL}{path}",
            json=json,
            timeout=2,
        )
        response.raise_for_status()
        return response

    except httpx.TimeoutException:
        st.error(
            "API’en svarede ikke hurtigt nok. "
            "Ved ændringer kan handlingen være gennemført. "
            "Opdatér oversigten, før du prøver igen."
        )

    except httpx.ConnectError:
        st.error("Kan ikke oprette forbindelse til API’en.")

    except httpx.HTTPStatusError as error:
        try:
            body = error.response.json()
            message = (
                body.get("error")
                if isinstance(body, dict)
                else None
            )
        except ValueError:
            message = None

        st.error(
            message
            or f"API’en returnerede en fejl: {error.response.status_code}"
        )

    except httpx.RequestError:
        st.error("Der opstod en netværksfejl under kommunikationen med API’en.")

    return None


# Navnet bevares mellem genkørsler i den aktuelle brugers session.
if "name" not in st.session_state:
    st.session_state["name"] = ""

st.title("Fredagsbarens events")
st.subheader("Alle events")

# Et klik genkører scriptet og henter dermed oversigten igen.
st.button("Opdatér oversigt")

response = api_request("GET", "/events")

if response is None:
    st.stop()

try:
    events = response.json()
except ValueError:
    st.error("API’en returnerede et svar, som ikke kunne læses som JSON.")
    st.stop()

if not isinstance(events, list):
    st.error("API’en returnerede ikke den forventede liste af events.")
    st.stop()


# Tabellen viser udvalgte felter og beregner ledige pladser i frontenden.
rows = []

for event in events:
    participant_count = len(event["participants"])

    rows.append({
        "Titel": event["title"],
        "Dato": event["date"],
        "Antal tilmeldte": participant_count,
        "Ledige pladser": event["capacity"] - participant_count,
    })

if rows:
    st.dataframe(rows, hide_index=True)
else:
    st.info("Der er endnu ingen events.")


if events:
    st.subheader("Tilmelding")

    selected_event = st.selectbox(
        "Vælg et event",
        options=events,
        format_func=lambda event: (
            f"{event['title']} · {event['date']}"
        ),
    )

    is_full = (
        len(selected_event["participants"])
        >= selected_event["capacity"]
    )

    name_column, signup_column = st.columns(
        [3, 1],
        vertical_alignment="bottom",
    )

    with name_column:
        st.text_input("Dit navn", key="name")

    with signup_column:
        signup_clicked = st.button(
            "Tilmeld",
            disabled=is_full,
        )

    name = st.session_state["name"].strip()

    if signup_clicked:
        if not name:
            st.error("Skriv dit navn i feltet først.")
        else:
            response = api_request(
                "POST",
                f"/events/{selected_event['id']}/signups",
                json={"name": name},
            )

            if response is not None:
                st.session_state["signup_feedback"] = {
                    "event_id": selected_event["id"],
                    "message": "Du er tilmeldt.",
                }
                st.rerun()

    if is_full:
        st.info("Eventet er fuldt.")

    st.write("Deltagere:")

    if selected_event["participants"]:
        for participant in selected_event["participants"]:
            participant_column, action_column = st.columns([3, 1])

            with participant_column:
                st.write(participant)

            # Afmelding tilbydes kun for navnet i brugerens navnefelt.
            if participant == name:
                with action_column:
                    unsubscribe_clicked = st.button(
                        "Afmeld",
                        key=f"unsubscribe_{selected_event['id']}_{participant}",
                    )

                    if unsubscribe_clicked:
                        encoded_name = quote(name, safe="")

                        response = api_request(
                            "DELETE",
                            f"/events/{selected_event['id']}"
                            f"/signups/{encoded_name}",
                        )

                        if response is not None:
                            st.session_state["signup_feedback"] = {
                                "event_id": selected_event["id"],
                                "message": "Du er afmeldt.",
                            }
                            st.rerun()
    else:
        st.info("Ingen er tilmeldt endnu.")

    # Beskeden vises under deltagerlisten efter opdatering af data.
    feedback = st.session_state.pop("signup_feedback", None)

    if feedback and feedback["event_id"] == selected_event["id"]:
        st.success(feedback["message"])


# Formularen er tilgængelig, selv når der ikke findes events.
st.subheader("Opret event")

with st.form("create_event_form"):
    title = st.text_input("Titel")
    date = st.date_input("Dato")
    capacity = st.number_input(
        "Antal pladser",
        min_value=1,
        value=10,
        step=1,
    )

    submitted = st.form_submit_button("Opret event")

if submitted:
    response = api_request(
        "POST",
        "/events",
        json={
            "title": title.strip(),
            "date": date.isoformat(),
            "capacity": capacity,
        },
    )

    if response is not None:
        st.session_state["create_feedback"] = "Eventet er oprettet."
        st.rerun()

create_feedback = st.session_state.pop("create_feedback", None)

if create_feedback:
    st.success(create_feedback)