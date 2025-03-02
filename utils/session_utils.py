from flask import session, jsonify

def save_trip_to_session(trip_plan, parameters):
    """Stores the trip plan in session with correct IDs."""
    session['trip_events'] = trip_plan
    session['trip_parameters'] = parameters
    session['locked_events'] = set()
    session.modified = True

def get_trip_from_session():
    """Retrieves the stored trip from session."""
    if 'trip_events' not in session:
        return jsonify({"success": False, "error": "No itinerary found"}), 404

    return session['trip_events']
