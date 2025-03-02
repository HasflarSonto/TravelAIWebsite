document.addEventListener("DOMContentLoaded", function () {
    fetchItinerary(); // Load the itinerary when the page loads

    function fetchItinerary() {
        fetch("/api/trip/events")
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayItinerary(data.events);
                } else {
                    console.error("No itinerary found:", data.error);
                    document.getElementById("itinerary-list").innerHTML = "<p>No itinerary found. Please create a trip first.</p>";
                }
            })
            .catch(error => console.error("Error fetching itinerary:", error));
    }

    function displayItinerary(events) {
        const itineraryList = document.getElementById("itinerary-list");
        itineraryList.innerHTML = "";

        if (events.length === 0) {
            itineraryList.innerHTML = "<p>No itinerary found. Please create a trip first.</p>";
            return;
        }

        let currentDate = "";
        events.forEach(event => {
            if (event.date !== currentDate) {
                currentDate = event.date;
                const dateHeader = document.createElement("h2");
                dateHeader.className = "itinerary-date";
                dateHeader.innerText = new Date(currentDate).toLocaleDateString("en-US", {
                    weekday: "long", year: "numeric", month: "long", day: "numeric"
                });
                itineraryList.appendChild(dateHeader);
            }

            const eventDiv = document.createElement("div");
            eventDiv.className = "itinerary-event";
            eventDiv.dataset.eventId = event.id; // Add event ID to the div

            eventDiv.innerHTML = `
                <div class="event-container">
                    <h3 class="event-title">${event.title || "Untitled Event"}</h3>
                    <p class="event-time">${event.start_time} → ${event.end_time}</p>
                    <p class="event-location">${event.location}</p>
                    <p class="event-cost">cost: ${event.cost}$</p>
                    <div class="event-buttons">
                        <button class="confirm-btn" data-id="${event.id}">Confirm</button>
                        <button class="modify-btn" data-id="${event.id}">Modify</button>
                    </div>
                </div>
                <div id="edit-form-${event.id}" class="edit-form-container" style="display: none;">
                    <div class="edit-form">
                        <h2>Edit Event</h2>
                        <div class="form-group">
                            <label for="editTitle-${event.id}">Title</label>
                            <input type="text" id="editTitle-${event.id}" value="${event.title}" required>
                        </div>
                        <div class="form-group">
                            <label for="editStartTime-${event.id}">Start Time</label>
                            <input type="time" id="editStartTime-${event.id}" value="${event.start_time}" required>
                        </div>
                        <div class="form-group">
                            <label for="editEndTime-${event.id}">End Time</label>
                            <input type="time" id="editEndTime-${event.id}" value="${event.end_time}" required>
                        </div>
                        <div class="form-group">
                            <label for="editLocation-${event.id}">Location</label>
                            <input type="text" id="editLocation-${event.id}" value="${event.location}" required>
                        </div>
                        <div class="form-group">
                            <label for="editCost-${event.id}">Cost ($)</label>
                            <input type="number" id="editCost-${event.id}" value="${event.cost}" step="0.01" required>
                        </div>
                        <div class="button-group">
                            <button class="save-btn" onclick="saveEventChanges('${event.id}')">Save</button>
                            <button class="delete-btn" onclick="deleteEvent('${event.id}')">Delete</button>
                            <button class="cancel-btn" onclick="cancelEdit('${event.id}')">Cancel</button>
                        </div>
                    </div>
                </div>
            `;

            itineraryList.appendChild(eventDiv);
        });

        addEventListeners();
    }

    function addEventListeners() {
        document.querySelectorAll(".confirm-btn").forEach(button => {
            button.addEventListener("click", function () {
                confirmEvent(this.getAttribute("data-id"));
            });
        });

        document.querySelectorAll(".modify-btn").forEach(button => {
            button.addEventListener("click", function () {
                modifyEvent(this.getAttribute("data-id"));
            });
        });
    }

    function confirmEvent(eventId) {
        fetch(`/api/trip/event/${eventId}/confirm`, { method: "POST" })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Event confirmed!");
                    fetchItinerary(); // Reload itinerary
                } else {
                    alert("Error confirming event: " + data.error);
                }
            })
            .catch(error => console.error("Error confirming event:", error));
    }

    function modifyEvent(eventId) {
        // Hide any other open edit forms
        document.querySelectorAll('.edit-form-container').forEach(form => {
            form.style.display = 'none';
        });
        
        // Show this event's edit form
        const editForm = document.getElementById(`edit-form-${eventId}`);
        editForm.style.display = 'block';
    }

    function saveEventChanges(eventId) {
        const formData = {
            title: document.getElementById(`editTitle-${eventId}`).value,
            start_time: document.getElementById(`editStartTime-${eventId}`).value,
            end_time: document.getElementById(`editEndTime-${eventId}`).value,
            location: document.getElementById(`editLocation-${eventId}`).value,
            cost: parseFloat(document.getElementById(`editCost-${eventId}`).value)
        };

        fetch(`/api/trip/event/${eventId}/modify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fetchItinerary();
            } else {
                alert('Error modifying event: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to modify event');
        });
    }

    function deleteEvent(eventId) {
        if (!confirm('Are you sure you want to delete this event?')) return;

        fetch(`/api/trip/event/${eventId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById(`edit-form-${eventId}`).style.display = 'none';
                fetchItinerary();
            } else {
                alert('Error deleting event: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to delete event');
        });
    }

    function cancelEdit(eventId) {
        document.getElementById(`edit-form-${eventId}`).style.display = 'none';
    }
});

