import os
from urllib.parse import quote

import httpx
import streamlit as st


# Miljøvariablen gør det muligt at bruge forskellige API-adresser lokalt og i Docker.
API_URL = os.environ.get("API_URL", "http://127.0.0.1:5001").rstrip("/")


def api_request(method, path, json=None):
    """Sender en HTTP-request og håndterer forbindelsesfejl og fejlsvar."""
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
            "Handlingen kan være gennemført. "
            "Opdatér oversigten, før du prøver igen."
        )

    except httpx.ConnectError:
        st.error("Kan ikke oprette forbindelse til API’en.")

    except httpx.HTTPStatusError as error:
        try:
            body = error.response.json()
            message = body.get("error") if isinstance(body, dict) else None
        except ValueError:
            message = None

        st.error(
            message
            or f"API’en returnerede en fejl: {error.response.status_code}"
        )

    except httpx.RequestError:
        st.error("Der opstod en netværksfejl under kommunikationen med API’en.")

    return None


def show_event_label(event_id):
    """Danner visningsteksten for et event uden at ændre det valgte ID."""
    event = events_by_id[event_id]
    return f"{event['title']} · {event['date']}"


if "name" not in st.session_state:
    st.session_state["name"] = ""

st.title("Fredagsbarens events")
st.subheader("Alle events")

# Et klik genkører scriptet og henter aktuelle data fra API’en.
st.button("Opdatér oversigt")

response = api_request("GET", "/events")

if response is None:
    st.stop()

try:
    events = response.json()
except ValueError:
    st.error("API’en returnerede ikke gyldig JSON.")
    st.stop()

if not isinstance(events, list):
    st.error("API’en returnerede ikke den forventede liste af events.")
    st.stop()

# Opslaget giver adgang til de nyeste eventdata ud fra et stabilt ID.
events_by_id = {event["id"]: event for event in events}
event_ids = list(events_by_id)

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

    # Et slettet event må ikke blive stående som valgt i sessionen.
    if st.session_state.get("selected_event_id") not in events_by_id:
        st.session_state["selected_event_id"] = event_ids[0]

    selected_event_id = st.selectbox(
        "Vælg et event",
        options=event_ids,
        format_func=show_event_label,
        key="selected_event_id",
    )

    selected_event = events_by_id[selected_event_id]
    participants = selected_event["participants"]
    is_full = len(participants) >= selected_event["capacity"]

    name_column, signup_column = st.columns(
        [3, 1],
        vertical_alignment="bottom",
    )

    with name_column:
        st.text_input("Dit navn", key="name")

    with signup_column:
        signup_clicked = st.button("Tilmeld", disabled=is_full)

    name = st.session_state["name"].strip()

    if signup_clicked:
        if not name:
            st.error("Skriv dit navn i feltet først.")
        else:
            response = api_request(
                "POST",
                f"/events/{selected_event_id}/signups",
                json={"name": name},
            )

            if response is not None:
                st.session_state["signup_feedback"] = {
                    "event_id": selected_event_id,
                    "message": f"{name} er tilmeldt.",
                }

                # Genkørslen henter den opdaterede liste før tabellen tegnes igen.
                st.rerun()

    if is_full:
        st.info("Eventet er fuldt.")

    st.write("Deltagere:")

    if participants:
        for participant in participants:
            participant_column, action_column = st.columns(
                [3, 1],
                vertical_alignment="center",
            )

            with participant_column:
                st.write(participant)

            with action_column:
                unsubscribe_clicked = st.button(
                    "Afmeld",
                    key=f"unsubscribe_{selected_event_id}_{participant}",
                )

                if unsubscribe_clicked:
                    # Navnet fra rækken bruges, uanset værdien i navnefeltet.
                    encoded_name = quote(participant, safe="")

                    response = api_request(
                        "DELETE",
                        f"/events/{selected_event_id}/signups/{encoded_name}",
                    )

                    if response is not None:
                        st.session_state["signup_feedback"] = {
                            "event_id": selected_event_id,
                            "message": f"{participant} er afmeldt.",
                        }
                        st.rerun()
    else:
        st.info("Ingen er tilmeldt endnu.")

    feedback = st.session_state.pop("signup_feedback", None)

    if feedback and feedback["event_id"] == selected_event_id:
        st.success(feedback["message"])


# Oprettelse er også tilgængelig, når eventlisten er tom.
st.subheader("Opret event")

with st.form("create_event_form"):
    title = st.text_input("Titel")
    date = st.date_input("Dato")
    capacity = st.slider(
    "Antal pladser",
    min_value=1,
    max_value=100,
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