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

if not ANTHROPIC_API_KEY:
    raise ValueError("❌ Error: ANTHROPIC_API_KEY is missing! Check your .env file.")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24).hex()


def extract_json_from_claude(response_text):
    """Extracts JSON from Claude responses and ensures it is valid."""
    match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)

    if match:
        json_str = match.group(1)  # Extract JSON block
    else:
        json_str = response_text  # Assume raw JSON if no markdown wrapper

    try:
        return json.loads(json_str)  # ✅ Parse JSON safely
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"❌ Raw Response: {response_text}")  # Debugging output
        return None  # Return None if JSON parsing fails

def generate_trip_plan(natural_input, parameters, use_test_data=False):
    """Calls Claude AI to generate a structured trip plan or returns test JSON."""
    
    if use_test_data:
        print("⚡ Using test JSON instead of Claude API")
        test_json = {
            "days": [
                {
                    "day": 1,
                    "date": "2025-03-14",
                    "location": "Rome",
                    "activities": [
                        {
                            "title": "Arrive in Rome, check into hotel",
                            "start_time": "9:00 AM",
                            "end_time": "10:00 AM",
                            "location": "Hotel Roma Central",
                            "cost": 0
                        },
                        {
                            "title": "Explore Trastevere",
                            "start_time": "11:00 AM",
                            "end_time": "1:00 PM",
                            "location": "Trastevere District",
                            "cost": 20
                        }
                    ],
                    "daily_budget": 50
                }
            ]
        }
        return test_json["days"]  # ✅ Always return a list

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
    You are an AI assistant that generates structured travel itineraries in JSON format. (keep it short)

    **TASK**:
    Generate a JSON itinerary with **specific start and end times** and a **unique location for each activity**.
    The response **must** follow this format:

    ```json
    {{
      "destination": "<destination>",
      "budget": {parameters['budget']},
      "travelers": {parameters['people_count']},
      "start_date": "{parameters['start_date']}",
      "end_date": "{parameters['end_date']}",
      "days": [
        {{
          "day": <day_number>,
          "date": "<YYYY-MM-DD>",
          "location": "<city_or_town>",
          "activities": [
            {{
              "title": "<activity_name>",
              "start_time": "<hh:mm AM/PM>",
              "end_time": "<hh:mm AM/PM>",
              "location": "<specific_activity_location>",
              "cost": <cost_in_dollars>
            }}
          ],
          "daily_budget": <total_cost_for_the_day>
        }}
      ]
    }}
    ```

    **RULES**:
    - **Each activity must have `start_time`, `end_time`, and a `location`.**
    - **Ensure the response is complete and valid JSON.**
    - **Do not include explanatory text or comments in the output. Only return raw JSON.**

    **User Request**: {natural_input}
    """

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
            system="Generate a JSON itinerary with specific start and end times.",
            messages=[{"role": "user", "content": prompt}]
        )

        json_data = extract_json_from_claude(response.content[0].text)

        if not json_data:
            print("❌ Error: JSON is None")
            return []

        # ✅ Handle list responses
        if isinstance(json_data, list):
            return json_data

        # ✅ Handle dictionary responses
        if isinstance(json_data, dict) and "days" in json_data and isinstance(json_data["days"], list):
            return json_data["days"]

        print("❌ Error: JSON format is incorrect. Expected 'days' as a list.")
        return []

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return []



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

        trip_plan = generate_trip_plan(natural_input, parameters)

        session['trip_events'] = trip_plan  # ✅ Store list directly
        session.modified = True

        return jsonify({'success': True, 'events': trip_plan})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trip/events', methods=['GET'])
def get_trip_events():
    """Returns the stored trip itinerary."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404

    events = session['trip_events']

    if not isinstance(events, list):
        return jsonify({"success": False, "error": "Itinerary format error"}), 500

    formatted_events = []
    for day in events:
        if isinstance(day, dict) and "activities" in day:
            for activity in day["activities"]:
                formatted_events.append({
                    "id": str(uuid.uuid4()),
                    "date": day.get("date", f"Day {day.get('day', '?')}"),
                    "location": activity.get("location", day.get("location", "Unknown")),  # ✅ Ensures each activity has a location
                    "title": activity["title"] if isinstance(activity, dict) else activity,
                    "start_time": activity.get("start_time", "TBD"),
                    "end_time": activity.get("end_time", "TBD"),
                    "cost": activity.get("cost", 0) if isinstance(activity, dict) else 0
                })

    return jsonify({"success": True, "events": formatted_events})





@app.route('/api/trip/event/<event_id>/confirm', methods=['POST'])
def confirm_event(event_id):
    """Marks an event as confirmed."""
    return jsonify({"success": True})


@app.route('/api/trip/event/<event_id>/modify', methods=['POST'])
def modify_event(event_id):
    """Modify an event."""
    return jsonify({"success": True})


@app.route('/api/trip/disruption', methods=['POST'])
def handle_disruption():
    """Handles disruptions by adjusting the trip schedule."""
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True)
