function handleMapClick(activities) {
    console.log('Map clicked with activities:', activities);
    if (activities && activities.length > 0) {
        initDayMap(activities);
    } else {
        console.error('No activities provided');
    }
}

function initDayMap(dayEvents) {
    console.log('=== initDayMap Debug Start ===');
    console.log('Received dayEvents:', dayEvents);

    const mapContainer = document.getElementById('day-map-container');
    console.log('Map container found:', !!mapContainer);
    
    if (!mapContainer) {
        console.error('Map container not found!');
        return;
    }

    // Log container dimensions
    console.log('Container dimensions:', {
        height: mapContainer.offsetHeight,
        width: mapContainer.offsetWidth
    });

    try {
        console.log('Initializing Google Maps...');
        const map = new google.maps.Map(mapContainer, {
            zoom: 13,
            styles: [
                {elementType: 'geometry', stylers: [{color: '#242f3e'}]},
                {elementType: 'labels.text.stroke', stylers: [{color: '#242f3e'}]},
                {elementType: 'labels.text.fill', stylers: [{color: '#746855'}]}
            ]
        });
        console.log('Map initialized successfully');

        // Create markers for each location
        const bounds = new google.maps.LatLngBounds();
        const markers = [];

        // Clear existing markers
        markers.forEach(marker => marker.setMap(null));
        markers.length = 0;

        console.log('Processing locations:', dayEvents.length);
        
        // Geocode each location
        dayEvents.forEach((event, index) => {
            console.log(`Geocoding location ${index + 1}:`, event.location);
            
            const geocoder = new google.maps.Geocoder();
            geocoder.geocode({ address: event.location }, (results, status) => {
                console.log(`Geocoding result for ${event.location}:`, status);
                
                if (status === 'OK') {
                    const position = results[0].geometry.location;
                    console.log('Position found:', position.toString());
                    
                    const marker = new google.maps.Marker({
                        map: map,
                        position: position,
                        label: `${index + 1}`,
                        title: event.title,
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 8,
                            fillColor: '#8796cf',
                            fillOpacity: 1,
                            strokeColor: '#ffffff',
                            strokeWeight: 2,
                        }
                    });

                    bounds.extend(position);
                    markers.push(marker);
                    console.log(`Marker ${index + 1} added`);

                    // Add info window
                    const infoWindow = new google.maps.InfoWindow({
                        content: `
                            <div style="color: #333; padding: 5px;">
                                <h3 style="margin: 0 0 5px 0;">${event.title}</h3>
                                <p style="margin: 0 0 5px 0;">${event.start_time} - ${event.end_time}</p>
                            </div>
                        `
                    });

                    marker.addListener('click', () => {
                        infoWindow.open(map, marker);
                    });

                    // Fit map to bounds after last marker is added
                    if (markers.length === dayEvents.length) {
                        console.log('All markers added, fitting bounds');
                        map.fitBounds(bounds);
                        map.setZoom(map.getZoom() - 0.5);
                        drawRoute(markers, map);
                    }
                } else {
                    console.error('Geocoding failed for:', event.location, 'Status:', status);
                }
            });
        });

    } catch (error) {
        console.error('Error in initDayMap:', error);
    }
    
    console.log('=== initDayMap Debug End ===');
}

function drawRoute(markers, map) {
    console.log('Drawing route between', markers.length, 'markers');
    const path = markers.map(marker => marker.getPosition());
    new google.maps.Polyline({
        path: path,
        geodesic: true,
        strokeColor: '#8796cf',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        map: map
    });
    console.log('Route drawn');
}

function closeDayMap() {
    const mapContainer = document.getElementById('day-map-container');
    if (mapContainer) {
        mapContainer.style.opacity = '0';
        setTimeout(() => {
            mapContainer.style.display = 'none';
        }, 300); // Wait for fade out animation
    }
} 