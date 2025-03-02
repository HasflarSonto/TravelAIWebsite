// Function to check if activity is dining-related
function isDiningActivity(text) {
    const diningKeywords = ['restaurant', 'pizza', 'lunch', 'dinner', 'cafe', 'dining', 'grimaldi'];
    console.log('Checking text:', text);
    const result = diningKeywords.some(keyword => text.toLowerCase().includes(keyword));
    console.log('Is dining activity:', result);
    return result;
}

// Function to handle showing/hiding the call button with delay
function checkForRestaurant(taskText) {
    const callDiv = document.getElementById('restaurant-call');
    if (!callDiv) {
        console.log('Call div not found');
        return;
    }

    console.log('Checking restaurant for:', taskText);
    if (isDiningActivity(taskText)) {
        console.log('Will show restaurant call button after delay');
        callDiv.style.opacity = '0';  // Start invisible
        callDiv.style.display = 'block';
        
        // Add delay and fade in
        setTimeout(() => {
            callDiv.style.transition = 'opacity 0.5s ease-in';
            callDiv.style.opacity = '1';
        }, 3000);
    } else {
        callDiv.style.display = 'none';
    }
}

// Function to make the call
function callRestaurant(phoneNumber) {
    if (confirm('Would you like to call the restaurant now?')) {
        window.location.href = `tel:${phoneNumber}`;
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Restaurant call script loaded');
    const callDiv = document.getElementById('restaurant-call');
    if (callDiv) {
        console.log('Restaurant call div found');
        // Initially hide the call button
        callDiv.style.display = 'none';
    }
}); 