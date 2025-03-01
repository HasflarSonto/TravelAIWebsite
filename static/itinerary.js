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

        events.forEach(event => {
            const eventDiv = document.createElement("div");
            eventDiv.className = "itinerary-event";
            eventDiv.innerHTML = `
                <h3>${event.title}</h3>
                <p><strong>Date:</strong> ${event.date} | <strong>Location:</strong> ${event.location}</p>
                <p><strong>Cost:</strong> $${event.cost}</p>
                <button class="confirm-btn" data-id="${event.id}">Confirm</button>
                <button class="modify-btn" data-id="${event.id}">Modify</button>
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
