from flask import Flask, render_template, request, jsonify, session
import os
import json
import re
import uuid
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24).hex()


def extract_json_from_claude(response_text):
    """Extracts valid JSON from Claude responses, removing markdown."""
    match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    return match.group(1) if match else response_text


def generate_trip_plan(natural_input, parameters):
    """Calls Claude AI to generate a structured trip plan."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-2",
        max_tokens=1000,
        temperature=0.7,
        system="Generate a JSON itinerary based on user input.",
        messages=[
            {"role": "user", "content": f"Plan a trip: {natural_input}. Constraints: {json.dumps(parameters)}"}
        ]
    )

    json_str = extract_json_from_claude(response.content[0].text)
    return json.loads(json_str)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/plan')
def plan():
    return render_template("plan.html")


@app.route('/itinerary')
def itinerary():
    return render_template("itinerary.html")


@app.route('/api/trip', methods=['POST'])
def create_trip():
    """API endpoint to create a new trip."""
    try:
        data = request.json
        required_fields = ["naturalLanguageInput", "budget", "peopleCount", "startDate", "endDate"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

        natural_input = data['naturalLanguageInput']
        parameters = {
            'budget': int(data['budget']),
            'people_count': int(data['peopleCount']),
            'start_date': data['startDate'],
            'end_date': data['endDate']
        }

        events = generate_trip_plan(natural_input, parameters)

        session['trip_events'] = events
        session['trip_parameters'] = parameters
        session['trip_natural_input'] = natural_input
        session.modified = True

        return jsonify({'success': True, 'events': events})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trip/events', methods=['GET'])
def get_trip_events():
    """Returns the current trip events."""
    return jsonify(session.get('trip_events', []))


@app.route('/api/trip/event/<event_id>/confirm', methods=['POST'])
def confirm_event(event_id):
    """Marks an event as confirmed."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No trip found"}), 404

    for event in session['trip_events']:
        if event['id'] == event_id:
            event['isConfirmed'] = True
            session.modified = True
            break

    return jsonify({"success": True})


@app.route('/api/trip/event/<event_id>/modify', methods=['POST'])
def modify_event(event_id):
    """Allows user to modify an event."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No trip found"}), 404

    data = request.json
    modification_text = data.get("modificationText", "").strip()
    if not modification_text:
        return jsonify({"success": False, "error": "Modification text required"}), 400

    for event in session['trip_events']:
        if event['id'] == event_id:
            event["modification_request"] = modification_text

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-2",
                max_tokens=500,
                temperature=0.7,
                system="Modify an event based on user input.",
                messages=[{"role": "user", "content": f"Modify this event: {json.dumps(event)} based on: {modification_text}"}]
            )

            modified_event = json.loads(extract_json_from_claude(response.content[0].text))

            if "title" not in modified_event or not modified_event["title"]:
                modified_event["title"] = event["title"]
            if "location" not in modified_event or not modified_event["location"]:
                modified_event["location"] = event["location"]

            session.modified = True
            return jsonify({"success": True, "modifiedEvent": modified_event})

    return jsonify({"success": False, "error": "Event not found"}), 404


@app.route('/api/trip/disruption', methods=['POST'])
def handle_disruption():
    """Handles disruptions by adjusting the trip schedule."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No trip found"}), 404

    data = request.json
    affected_event_id = data.get("eventId")
    disruption_details = data.get("details")

    if not affected_event_id or not disruption_details:
        return jsonify({"success": False, "error": "Event ID and details are required"}), 400

    events = session['trip_events']
    for i, event in enumerate(events):
        if event['id'] == affected_event_id:
            event_index = i
            break
    else:
        return jsonify({"success": False, "error": "Event not found"}), 404

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-2",
        max_tokens=700,
        temperature=0.7,
        system="Reschedule events dynamically based on disruptions.",
        messages=[
            {"role": "user", "content": f"Disruption: {disruption_details}. Update events: {json.dumps(events[event_index:event_index+3])}"}
        ]
    )

    adjusted_events = json.loads(extract_json_from_claude(response.content[0].text))
    session['trip_events'][event_index:event_index+3] = adjusted_events
    session.modified = True

    return jsonify({"success": True, "updatedEvents": adjusted_events})


if __name__ == '__main__':
    app.run(debug=True)
