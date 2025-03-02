from flask import Flask, render_template, request, jsonify, session
import os
import json
import re
import uuid
from dotenv import load_dotenv
import anthropic
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("❌ Error: ANTHROPIC_API_KEY is missing! Check your .env file.")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(24).hex()


def extract_json_from_claude(response_text):
    """Extracts JSON from Claude responses and ensures it is valid."""
    # Look for JSON in markdown code blocks
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text, re.DOTALL)
    
    if match:
        json_str = match.group(1).strip()  # Extract JSON block
    else:
        # Try to find JSON-like content with curly braces
        match = re.search(r'(\{[\s\S]*\})', response_text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = response_text  # Assume raw JSON if no wrapper detected
    
    try:
        return json.loads(json_str)  # Parse JSON safely
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"❌ Raw Response: {response_text}")  
        
        # Attempt to fix common JSON errors
        try:
            # Replace single quotes with double quotes if needed
            fixed_json = json_str.replace("'", '"')
            return json.loads(fixed_json)
        except:
            # If all parsing attempts fail
            return None


def validate_trip_data(json_data):
    """Validates and standardizes the trip data structure."""
    if not json_data:
        return []
        
    # Handle if it's already a list of days
    if isinstance(json_data, list):
        days = json_data
    # Extract days from the object if available
    elif isinstance(json_data, dict) and "days" in json_data and isinstance(json_data["days"], list):
        days = json_data["days"]
    else:
        print("❌ Error: JSON format is incorrect. Expected 'days' as a list.")
        return []
    
    # Validate and standardize each day
    standardized_days = []
    for day_index, day in enumerate(days):
        if not isinstance(day, dict):
            continue
            
        std_day = {
            "day": day.get("day", day_index + 1),
            "date": day.get("date", ""),
            "location": day.get("location", "TBD"),
            "activities": [],
            "daily_budget": day.get("daily_budget", 0)
        }
        
        # Validate activities
        if "activities" in day and isinstance(day["activities"], list):
            for activity in day["activities"]:
                if not isinstance(activity, dict):
                    continue
                    
                std_activity = {
                    "title": activity.get("title", "Untitled Activity"),
                    "start_time": activity.get("start_time", "TBD"),
                    "end_time": activity.get("end_time", "TBD"),
                    "location": activity.get("location", std_day["location"]),
                    "cost": float(activity.get("cost", 0))
                }
                std_day["activities"].append(std_activity)
                
        standardized_days.append(std_day)
    
    return standardized_days


def generate_trip_plan(natural_input, parameters, use_test_data=False):
    """Calls Claude AI to generate a structured trip plan including travel logistics.""" 
    
    if use_test_data:
        print("⚡ Using test JSON instead of Claude API") 
        test_json = {
            "days": [
                {
                    "day": 1,
                    "date": "2025-03-14",
                    "location": parameters["start_location"],
                    "activities": [
                        {
                            "title": f"Depart from {parameters['start_location']}",
                            "start_time": "6:00 AM",
                            "end_time": "9:00 AM",
                            "location": f"{parameters['start_location']} International Airport",
                            "cost": 300
                        },
                        {
                            "title": f"Flight to {parameters['end_location']}",
                            "start_time": "10:00 AM",
                            "end_time": "2:00 PM",
                            "location": f"{parameters['end_location']} International Airport",
                            "cost": 700
                        }
                    ],
                    "daily_budget": 1000
                }
            ]
        }
        return validate_trip_data(test_json)

    # Parse dates to generate accurate itinerary dates
    try:
        start_date = datetime.strptime(parameters['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(parameters['end_date'], "%Y-%m-%d")
        trip_duration = (end_date - start_date).days + 1
    except ValueError:
        # Default to a 3-day trip if date parsing fails
        start_date = datetime.now()
        trip_duration = 3
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
    You are a professional travel planner creating a detailed, realistic travel itinerary.

    **TASK**: 
    Create a JSON-formatted travel itinerary from {parameters['start_location']} to {parameters['end_location']} 
    based on the user's request: "{natural_input}"

    **ITINERARY REQUIREMENTS**:
    - Trip starts on {parameters['start_date']} and ends on {parameters['end_date']}
    - Budget: ${parameters['budget']} total for {parameters['people_count']} traveler(s)
    - Include realistic transportation from {parameters['start_location']} to {parameters['end_location']}
    - Include local attractions, food options, and activities at {parameters['end_location']}
    - Every activity must include: title, start time, end time, location, and estimated cost
    - Every day must include: day number, date (YYYY-MM-DD), location, and a list of activities

    **IMPORTANT TRAVEL PLANNING GUIDELINES**:
    1. Research realistic travel times between {parameters['start_location']} and {parameters['end_location']}
    2. Consider the appropriate mode of transportation (flight, train, car, etc.)
    3. Include check-in/check-out times for accommodations
    4. Plan meals at appropriate times
    5. Allow sufficient time between activities
    6. Distribute the budget realistically across transportation, accommodation, food, and activities
    7. Include popular tourist attractions and local experiences

    **FORMAT YOUR RESPONSE AS VALID JSON ONLY**:
    ```json
    {{
      "destination": "{parameters['end_location']}",
      "budget": {parameters['budget']},
      "travelers": {parameters['people_count']},
      "start_date": "{parameters['start_date']}",
      "end_date": "{parameters['end_date']}",
      "days": [
        {{
          "day": 1,
          "date": "{start_date.strftime('%Y-%m-%d')}",
          "location": "{parameters['start_location']}",
          "activities": [
            {{
              "title": "Flight from {parameters['start_location']} to {parameters['end_location']}",
              "start_time": "10:00 AM",
              "end_time": "2:00 PM",
              "location": "{parameters['start_location']} International Airport",
              "cost": 700
            }}
          ],
          "daily_budget": 1000
        }}
      ]
    }}
    ```
    """

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",  # Using latest Claude model
            max_tokens=4000,
            temperature=0.7,
            system="You are a travel planning assistant that creates detailed, realistic travel itineraries with accurate transportation times, costs, and activities.",
            messages=[{"role": "user", "content": prompt}]
        )

        json_data = extract_json_from_claude(response.content[0].text)
        return validate_trip_data(json_data)

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return []


@app.route('/api/trip', methods=['POST'])
def create_trip():
    """API endpoint to create a new trip considering start & end locations."""
    try:
        data = request.json
        required_fields = ["naturalLanguageInput", "budget", "peopleCount", "startDate", "endDate", "startLocation", "endLocation"]
        
        # Validate all required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

        # Sanitize and prepare parameters
        natural_input = data['naturalLanguageInput'].strip()
        
        try:
            parameters = {
                'budget': int(float(data['budget'])),
                'people_count': int(data['peopleCount']),
                'start_date': data['startDate'],
                'end_date': data['endDate'],
                'start_location': data['startLocation'].strip(),
                'end_location': data['endLocation'].strip()
            }
        except (ValueError, TypeError) as e:
            return jsonify({"success": False, "error": f"Invalid parameter format: {str(e)}"}), 400

        # Generate the trip plan
        trip_plan = generate_trip_plan(natural_input, parameters)
        
        if not trip_plan:
            return jsonify({"success": False, "error": "Failed to generate trip plan"}), 500

        # Store in session
        session['trip_events'] = trip_plan
        session['trip_parameters'] = parameters
        session['trip_natural_input'] = natural_input
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
    total_cost = 0
    
    for day in events:
        if isinstance(day, dict) and "activities" in day:
            for activity in day["activities"]:
                activity_cost = float(activity.get("cost", 0)) if isinstance(activity, dict) else 0
                total_cost += activity_cost
                
                event_id = str(uuid.uuid4())
                formatted_events.append({
                    "id": event_id,
                    "day": day.get("day", "?"),
                    "date": day.get("date", f"Day {day.get('day', '?')}"),
                    "location": activity.get("location", day.get("location", "Unknown")),
                    "title": activity["title"] if isinstance(activity, dict) else str(activity),
                    "start_time": activity.get("start_time", "TBD"),
                    "end_time": activity.get("end_time", "TBD"),
                    "cost": activity_cost,
                    "confirmed": False
                })

    # Add summary information
    summary = {
        "total_cost": total_cost,
        "total_days": len(events),
        "start_location": session.get('trip_parameters', {}).get('start_location', "Unknown"),
        "end_location": session.get('trip_parameters', {}).get('end_location', "Unknown"),
        "budget": session.get('trip_parameters', {}).get('budget', 0),
        "people_count": session.get('trip_parameters', {}).get('people_count', 1)
    }

    return jsonify({
        "success": True, 
        "events": formatted_events,
        "summary": summary
    })


@app.route('/api/trip/event/<event_id>/confirm', methods=['POST'])
def confirm_event(event_id):
    """Marks an event as confirmed and updates session data."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
        
    # Get the event data from the request
    data = request.json or {}
    confirmed = data.get('confirmed', True)
    
    # Update session data to mark this event as confirmed
    # In a real app, you would find and update the specific event
    # For now, we'll just return success
    
    return jsonify({
        "success": True,
        "event_id": event_id,
        "confirmed": confirmed
    })


@app.route('/api/trip/event/<event_id>/modify', methods=['POST'])
def modify_event(event_id):
    """Modify an event's details."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
        
    data = request.json or {}
    required_fields = ["title", "start_time", "end_time", "location", "cost"]
    
    # Validate required fields
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
    
    # In a real app, you would find and update the specific event in the session
    # For now, we'll just return success with the modified data
    
    return jsonify({
        "success": True,
        "event_id": event_id,
        "modified_event": data
    })


@app.route('/api/trip/disruption', methods=['POST'])
def handle_disruption():
    """Handles disruptions by adjusting the trip schedule."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
        
    data = request.json or {}
    
    if "disruption_type" not in data or "affected_events" not in data:
        return jsonify({"success": False, "error": "Missing disruption details"}), 400
        
    disruption_type = data["disruption_type"]
    affected_events = data["affected_events"]
    
    # Here you would call Claude API to regenerate the affected parts of the itinerary
    # For now, we'll just return a placeholder response
    
    return jsonify({
        "success": True,
        "message": f"Trip adjusted due to {disruption_type}",
        "affected_events": affected_events
    })


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/plan')
def plan():
    return render_template("plan.html")


@app.route('/itinerary')
def itinerary():
    return render_template("itinerary.html")


if __name__ == '__main__':
    app.run(debug=True)