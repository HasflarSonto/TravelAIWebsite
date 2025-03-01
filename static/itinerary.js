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
        itineraryList.innerHTML = ""; // Clear previous content

        if (events.length === 0) {
            itineraryList.innerHTML = "<p>No itinerary found. Please create a trip first.</p>";
            return;
        }

        let currentDate = "";
        events.forEach(event => {
            // Insert a date header when the date changes
            if (event.date !== currentDate) {
                currentDate = event.date;
                const dateHeader = document.createElement("h2");
                dateHeader.className = "itinerary-date";
                dateHeader.innerText = new Date(currentDate).toLocaleDateString("en-US", {
                    weekday: "long", year: "numeric", month: "long", day: "numeric"
                });
                itineraryList.appendChild(dateHeader);
            }

            // Create an event card
            const eventDiv = document.createElement("div");
            eventDiv.className = "itinerary-event";

            eventDiv.innerHTML = `
                <div class="event-container">
                    <h3 class="event-title">${event.title || "Untitled Event"}</h3>
                    <p class="event-time">${event.start_time} → ${event.end_time}</p>
                    <p class="event-location">${event.location}</p>
                    <div class="event-buttons">
                        <button class="confirm-btn" data-id="${event.id}">Confirm</button>
                        <button class="modify-btn" data-id="${event.id}">Modify</button>
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
        const modificationText = prompt("Describe how you'd like to modify this event:");
        if (!modificationText) return;

        fetch(`/api/trip/event/${eventId}/modify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ modificationText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Event modified!");
                fetchItinerary();
            } else {
                alert("Error modifying event: " + data.error);
            }
        })
        .catch(error => console.error("Error modifying event:", error));
    }
});
