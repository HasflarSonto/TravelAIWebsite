from flask import Blueprint, request, jsonify, session
from utils.session_utils import get_trip_from_session

event_routes = Blueprint("event_routes", __name__)

@event_routes.route('/api/trip/event/<event_id>/modify', methods=['POST'])
def modify_event(event_id):
    """Modifies an event's details."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404
        
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    events = session['trip_events']
    
    # Find and update the specific event
    for day in events:
        for activity in day['activities']:
            if str(activity.get('id')) == str(event_id):  # Convert both to strings for comparison
                activity.update({
                    'title': data['title'],
                    'start_time': data['start_time'],
                    'end_time': data['end_time'],
                    'location': data['location'],
                    'cost': data['cost']
                })
                session.modified = True
                return jsonify({
                    "success": True,
                    "modifiedEvent": activity
                })
    
    return jsonify({"success": False, "error": "Event not found"}), 404
