from flask import Blueprint, jsonify, session
from utils.session_utils import get_trip_from_session

trip_routes = Blueprint("trip_routes", __name__)

@trip_routes.route('/api/trip/events', methods=['GET'])
def get_trip_events():
    """Returns the stored trip itinerary."""
    events = get_trip_from_session()

    formatted_events = []
    for day in events:
        if isinstance(day, dict) and "activities" in day:
            for activity in day["activities"]:
                formatted_events.append({
                    "id": activity["id"],  # ✅ Use stored ID
                    "date": day.get("date", f"Day {day.get('day', '?')}"),
                    "location": activity.get("location", day.get("location", "Unknown")),
                    "title": activity["title"],
                    "start_time": activity.get("start_time", "TBD"),
                    "end_time": activity.get("end_time", "TBD"),
                    "cost": activity.get("cost", 0)
                })

    return jsonify({"success": True, "events": formatted_events})
