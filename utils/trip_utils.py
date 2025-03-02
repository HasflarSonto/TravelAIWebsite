import json
import anthropic
import uuid
import re
from flask import session

def extract_json_from_claude(response_text):
    """Extracts JSON from Claude responses and ensures it is valid."""
    match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    json_str = match.group(1) if match else response_text  # Extract JSON block

    try:
        return json.loads(json_str)  # ✅ Parse JSON safely
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"❌ Raw Response: {response_text}")  # Debugging output
        return None  # Return None if JSON parsing fails

def generate_trip_plan(natural_input, parameters):
    """Calls Claude AI to generate a structured trip plan including travel logistics."""
    client = anthropic.Anthropic(api_key=session.get("ANTHROPIC_API_KEY"))

    prompt = f"""
    You are an AI assistant that generates structured travel itineraries in JSON format.

    **TASK**:
    - Generate a JSON itinerary for travel from `{parameters['start_location']}` to `{parameters['end_location']}`.
    - **Each event must have a start time, end time, and a unique ID**.
    - **Return only valid JSON format.**

    **User Request**: {natural_input}
    """

    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.7,
            system="Generate a JSON itinerary with unique IDs.",
            messages=[{"role": "user", "content": prompt}]
        )

        json_data = extract_json_from_claude(response.content[0].text)

        if not json_data or "days" not in json_data:
            print("❌ Error: JSON format incorrect.")
            return []

        trip_plan = json_data["days"]

        # ✅ Assign sequential IDs
        event_id = 1
        for day in trip_plan:
            for activity in day.get("activities", []):
                activity["id"] = str(event_id)  # Assign unique ID
                event_id += 1

        return trip_plan

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return []
