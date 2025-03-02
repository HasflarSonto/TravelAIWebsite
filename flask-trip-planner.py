from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
            model="claude-3-opus-20240229",  # Updated to correct model name
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


def generate_trip_suggestions(parameters):
    """Generates high-level activity suggestions with alternatives."""
    try:
        print("⚡ Starting suggestion generation...")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        # Calculate slots needed
        try:
            start_date = datetime.strptime(parameters['start_date'], "%Y-%m-%d")
            end_date = datetime.strptime(parameters['end_date'], "%Y-%m-%d")
            trip_days = (end_date - start_date).days + 1
            suggestions_count = trip_days * 2  # 2 activities per day
        except:
            suggestions_count = 4  # Default to 2 days worth
        
        print(f"📅 Generating {suggestions_count} time slots with alternatives...")
        
        prompt = f"""
        Generate exactly {suggestions_count} activity suggestions for tourists visiting {parameters['end_location']}.
        Each activity should have ONE alternative option (total of {suggestions_count * 2} activities).

        Trip Details:
        - Location: {parameters['end_location']}
        - Duration: {trip_days} days ({suggestions_count} activities needed)
        - Budget: ${parameters['budget']} total for {parameters['people_count']} people
        - Dates: {parameters['start_date']} to {parameters['end_date']}
        - Preferences: {parameters.get('natural_language_input', 'No specific preferences')}

        IMPORTANT: ALL suggestions MUST be real, existing places or activities in {parameters['end_location']}.
        Do NOT suggest generic activities or places from other locations.

        For each time slot provide:
        1. One main activity in {parameters['end_location']}
        2. One alternative activity in {parameters['end_location']} that is:
           - In the same category (e.g., both cultural, both outdoor)
           - At a similar time of day
           - Different from the main activity

        Return ONLY valid JSON matching this EXACT format:
        {{
            "time_slots": [
                {{
                    "category": "Category name",
                    "best_time": "Morning/Afternoon/Evening",
                    "options": [
                        {{
                            "title": "Activity in {parameters['end_location']}",
                            "description": "Brief description",
                            "duration": "2-3 hours",
                            "cost": 45,
                            "location": "Specific location name in {parameters['end_location']}"
                        }},
                        {{
                            "title": "Alternative in {parameters['end_location']}",
                            "description": "Brief description",
                            "duration": "2-3 hours",
                            "cost": 45,
                            "location": "Different specific location in {parameters['end_location']}"
                        }}
                    ]
                }}
            ]
        }}
        """

        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
            system=f"You are a local tour guide in {parameters['end_location']}. Only suggest real, specific places and activities in {parameters['end_location']}.",
            messages=[{"role": "user", "content": prompt}]
        )

        data = extract_json_from_claude(response.content[0].text)
        
        if not data or "time_slots" not in data:
            print("❌ Error: Invalid suggestions format")
            return []
            
        # Format suggestions for frontend
        formatted_suggestions = []
        for i, slot in enumerate(data["time_slots"]):
            for j, option in enumerate(slot["options"]):
                suggestion = {
                    "id": f"sug_{i}_{j}",
                    "title": option["title"],
                    "description": option["description"],
                    "duration": option["duration"],
                    "cost": option["cost"],
                    "category": slot["category"],
                    "location": option["location"],
                    "best_time": slot["best_time"],
                    "slot_index": i,
                    "option_index": j
                }
                formatted_suggestions.append(suggestion)
        
        print(f"✅ Generated {len(formatted_suggestions)} total suggestions")
        return formatted_suggestions

    except Exception as e:
        print(f"❌ Error generating suggestions: {str(e)}")
        return []


def generate_final_itinerary(selected_activities, parameters):
    """Generates a detailed itinerary based on selected activities."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    activities_str = "\n".join([
        f"- {act['title']} ({act['duration']}, {act['best_time']}, at {act['location']})"
        for act in selected_activities
    ])
    
    prompt = f"""
    Create a detailed day-by-day itinerary incorporating these selected activities:
    {activities_str}

    Trip Parameters:
    - Start: {parameters['start_date']} in {parameters['start_location']}
    - End: {parameters['end_date']} in {parameters['end_location']}
    - Budget: ${parameters['budget']}
    - Group Size: {parameters['people_count']}

    Requirements:
    1. Include all selected activities
    2. Add necessary travel time between locations
    3. Include meal breaks if not part of activities
    4. Balance the schedule across available days
    5. Consider activity timing preferences (morning/afternoon/evening)
    6. Include specific start/end times for each activity
    
    Return ONLY valid JSON matching this structure:
    {{
        "days": [
            {{
                "day": 1,
                "date": "YYYY-MM-DD",
                "location": "Location name",
                "activities": [
                    {{
                        "title": "Activity name",
                        "start_time": "HH:MM AM/PM",
                        "end_time": "HH:MM AM/PM",
                        "location": "Specific location",
                        "cost": cost_in_dollars
                    }}
                ]
            }}
        ]
    }}
    """

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        itinerary = extract_json_from_claude(response.content[0].text)
        if not itinerary or "days" not in itinerary:
            print("❌ Error: Invalid itinerary format")
            return []
            
        return itinerary["days"]

    except Exception as e:
        print(f"❌ Error generating itinerary: {e}")
        return []


@app.route('/api/trip', methods=['POST'])
def create_trip():
    """Creates initial trip suggestions."""
    data = request.json
    
    # Standardize parameter names
    parameters = {
        'start_location': data.get('startLocation'),
        'end_location': data.get('endLocation'),
        'start_date': data.get('startDate'),
        'end_date': data.get('endDate'),
        'budget': data.get('budget'),
        'people_count': data.get('peopleCount'),
        'natural_language_input': data.get('naturalLanguageInput')
    }
    
    # Validate all required parameters are present
    if not all(parameters.values()):
        return jsonify({
            "success": False, 
            "error": "Missing required parameters"
        }), 400
    
    # Store trip parameters in session
    session['trip_parameters'] = parameters
    
    # Generate suggestions
    try:
        suggestions = generate_trip_suggestions(parameters)
        if isinstance(suggestions, tuple):  # If it's an error response
            return suggestions
            
        # Store the suggestions directly (they're already in the right format)
        session['trip_suggestions'] = suggestions
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Error in create_trip: {str(e)}")
        return jsonify({
            "success": False, 
            "error": "Failed to generate suggestions"
        }), 500


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


def convert_to_minutes(time_str):
    """Convert time string to minutes since midnight for sorting"""
    try:
        # If time is in 12-hour format (e.g., "8:00 AM")
        if 'AM' in time_str.upper() or 'PM' in time_str.upper():
            time_obj = datetime.strptime(time_str, '%I:%M %p')
        # If time is in 24-hour format (e.g., "14:00")
        else:
            time_obj = datetime.strptime(time_str, '%H:%M')
        return time_obj.hour * 60 + time_obj.minute
    except ValueError:
        return 0


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/plan')
def plan():
    return render_template('plan.html')


@app.route('/itinerary')
def show_itinerary():
    if 'trip_events' not in session:
        return redirect(url_for('home'))
        
    trip_events = session['trip_events']
    
    formatted_events = []
    for day in trip_events:
        # Ensure all activities have IDs
        for activity in day['activities']:
            if 'id' not in activity or not activity['id']:
                activity['id'] = str(uuid.uuid4())
        
        # Sort activities by converting their times to minutes
        sorted_activities = sorted(
            day['activities'],
            key=lambda x: convert_to_minutes(x['start_time'])
        )
        
        formatted_day = {
            'date': day['date'],
            'activities': sorted_activities
        }
        formatted_events.append(formatted_day)
    
    session.modified = True
    return render_template('itinerary.html', trip_events=formatted_events)


@app.route('/suggestions')
def suggestions():
    """Renders the suggestions page."""
    if 'trip_parameters' not in session:
        return redirect(url_for('plan'))
    return render_template("suggestions.html")


@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Returns AI-generated activity suggestions for the trip."""
    try:
        if 'trip_suggestions' in session:
            return jsonify({
                "success": True,
                "suggestions": session['trip_suggestions']
            })
            
        if 'trip_parameters' not in session:
            print("❌ No trip parameters found in session")
            return jsonify({
                "success": False,
                "error": "No trip parameters found"
            }), 404

        parameters = session['trip_parameters']
        print(f"📋 Retrieved parameters from session: {parameters}")
        
        suggestions = generate_trip_suggestions(parameters)
        session['trip_suggestions'] = suggestions
        
        return jsonify({
            "success": True,
            "suggestions": suggestions
        })

    except Exception as e:
        print(f"❌ Error in get_suggestions route: {str(e)}")
        import traceback
        print(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/suggestions/select', methods=['POST'])
def select_suggestions():
    """Generates final itinerary from selected suggestions."""
    if 'trip_parameters' not in session:
        return jsonify({"success": False, "error": "No trip parameters found"}), 404
        
    data = request.json
    selected_activities = data.get('selected_activities', [])
    
    if not selected_activities:
        return jsonify({"success": False, "error": "No activities selected"}), 400
    
    try:
        parameters = session['trip_parameters']
        itinerary = generate_final_itinerary(selected_activities, parameters)
        
        if not itinerary:
            return jsonify({"success": False, "error": "Failed to generate itinerary"}), 500
            
        # Store the generated itinerary in session
        session['trip_events'] = itinerary
        print(f"✅ Itinerary generated with {len(itinerary)} days and {len(selected_activities)} activities")
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Error generating final itinerary: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/suggestions/alternative', methods=['POST'])
def generate_alternative_suggestion():
    """Generates an alternative suggestion based on rejected activity."""
    if 'trip_parameters' not in session:
        return jsonify({"success": False, "error": "No trip parameters found"}), 404
        
    data = request.json
    rejected = data['rejected']
    previous_suggestions = data.get('previous_suggestions', [])
    parameters = session['trip_parameters']
    
    prompt = f"""
    Generate ONE alternative activity suggestion to replace: "{rejected['title']}"
    
    Location: {parameters['end_location']}
    Requirements:
    - Similar category: {rejected['category']}
    - Similar time of day: {rejected['best_time']}
    - Similar duration: {rejected['duration']}
    - Must be a DIFFERENT activity from these previously suggested activities: {', '.join(previous_suggestions)}
    - Must be a real place/activity in {parameters['end_location']}
    - Should fit within a budget of ${parameters['budget']} for {parameters['people_count']} people
    
    DO NOT suggest any of these previous activities:
    {previous_suggestions}
    
    For example:
    - If a museum was rejected, suggest a different cultural venue
    - If a restaurant was rejected, suggest a different cuisine or dining experience
    - If an outdoor activity was rejected, suggest a different outdoor activity
    
    Return ONLY valid JSON matching this EXACT format:
    {{
        "title": "New Activity Name",
        "description": "Brief 1-2 sentence description",
        "duration": "{rejected['duration']}",
        "cost": similar_cost_to_original,
        "category": "{rejected['category']}",
        "location": "Specific location name and address in {parameters['end_location']}",
        "best_time": "{rejected['best_time']}"
    }}
    """
    
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.9,  # Increased temperature for more variety
            system="You are a local tour guide generating alternative activity suggestions. Never repeat a previously suggested activity.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        alternative = extract_json_from_claude(response.content[0].text)
        
        # Validate the alternative suggestion
        if not alternative:
            return jsonify({"success": False, "error": "Failed to generate alternative"}), 500
            
        # Check if this is a duplicate suggestion
        if alternative.get('title') in previous_suggestions:
            return jsonify({"success": False, "error": "Generated a duplicate suggestion"}), 500
            
        # Ensure the suggestion is for the correct location
        if parameters['end_location'].lower() not in alternative['location'].lower():
            return jsonify({"success": False, "error": "Generated suggestion for wrong location"}), 500
            
        # Add a unique ID to the alternative
        alternative['id'] = f"alt_{uuid.uuid4().hex[:8]}"
        
        print(f"✅ Generated alternative: {alternative['title']}")
        return jsonify({
            "success": True,
            "alternative": alternative
        })
        
    except Exception as e:
        print(f"❌ Error generating alternative: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/trip/event/<event_id>/modify', methods=['POST'])
def modify_event(event_id):
    if not event_id:
        return jsonify({"success": False, "error": "No event ID provided"}), 400
        
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
        
    data = request.json
    
    events = session['trip_events']
    for day in events:
        for activity in day['activities']:
            if str(activity.get('id')) == str(event_id):
                activity.update({
                    'title': data['title'],
                    'start_time': data['start_time'],
                    'end_time': data['end_time'],
                    'location': data['location'],
                    'cost': data['cost']
                })
                session.modified = True
                return jsonify({"success": True, "modifiedEvent": activity})
    
    return jsonify({"success": False, "error": "Event not found"}), 404


@app.route('/api/trip/event/<event_id>/delete', methods=['DELETE'])
def delete_event(event_id):
    """Deletes an event from the trip."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
    
    try:
        # Find and remove the event from trip_events
        trip_events = session['trip_events']
        for day in trip_events:
            day['activities'] = [activity for activity in day['activities'] 
                               if str(activity.get('id')) != str(event_id)]
        
        session['trip_events'] = trip_events
        session.modified = True
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Error deleting event: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/trip/event/add', methods=['POST'])
def add_event():
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
    
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    new_event = {
        'id': str(uuid.uuid4()),
        'title': data['title'],
        'start_time': data['start_time'],
        'end_time': data['end_time'],
        'location': data['location'],
        'cost': data['cost']
    }
    
    # Find the correct day and add the event
    events = session['trip_events']
    for day in events:
        if day['date'] == data['day_date']:
            day['activities'].append(new_event)
            session.modified = True
            return jsonify({"success": True, "newEvent": new_event})
    
    return jsonify({"success": False, "error": "Day not found"}), 404


@app.route('/todos')
def todos():
    """Renders the todos page."""
    if 'trip_events' not in session:
        return redirect(url_for('plan'))
    return render_template('todos.html', trip_events=session.get('trip_events', []))


@app.route('/api/trip/todos/save', methods=['POST'])
def save_todos():
    """Saves the todo state for an activity."""
    try:
        data = request.json
        activity_id = data.get('activityId')
        todos = data.get('todos', [])
        event_confirmed = data.get('eventConfirmed', False)
        
        # Update the todos in session
        trip_events = session.get('trip_events', [])
        for day in trip_events:
            for activity in day['activities']:
                if activity['id'] == activity_id:
                    activity['todos'] = todos
                    activity['confirmed'] = event_confirmed
                    break
        
        session['trip_events'] = trip_events
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/trip/generate', methods=['POST'])
def generate_trip():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['destination', 'start_date', 'end_date', 'budget']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing {field}'}), 400
        
        # Store trip data in session
        session['trip_data'] = {
            'destination': data['destination'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'budget': float(data['budget'])
        }
        
        # Initialize empty trip events
        session['trip_events'] = []
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/todo-help', methods=['POST'])
def get_ai_todo_help():
    """Generates AI assistance for a specific todo/task."""
    try:
        data = request.json
        task = data.get('task')
        
        if not task:
            return jsonify({
                "success": False,
                "error": "No task provided"
            }), 400

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = f"""
        As a travel planning assistant, provide helpful advice for this travel task:
        "{task}"

        Consider:
        1. Best practices and tips
        2. Common pitfalls to avoid
        3. Useful resources or websites
        4. Timing recommendations
        5. Money-saving tips if applicable

        Keep the response concise but informative, focusing on practical advice.
        """

        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=500,
            temperature=0.7,
            system="You are a helpful travel planning assistant providing practical advice for specific travel tasks.",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_response = response.content[0].text.strip()
        
        return jsonify({
            "success": True,
            "response": ai_response
        })

    except Exception as e:
        print(f"❌ Error getting AI assistance: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get AI assistance"
        }), 500


if __name__ == '__main__':
    app.run(debug=True)