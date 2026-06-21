let map;
let markers = [];

function initMap() {
	// Default center (can be user's location later)
	const defaultCenter = { lat: 3.139, lng: 101.6869 };
	let center = defaultCenter;

	// Try to get user's location
	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(
			(position) => {
				center = {
					lat: position.coords.latitude,
					lng: position.coords.longitude,
				};
				map.setCenter(center);
			},
			() => {
				// Geolocation failed, keep default
				console.warn("Geolocation not available, using default.");
			},
		);
	}

	map = new google.maps.Map(document.getElementById("map"), {
		center: center,
		zoom: 12,
	});

	// servicesData is a JSON array passed from Flask
	const services = JSON.parse(
		document.getElementById("services-data").textContent,
	);

	services.forEach((service) => {
		if (service.latitude && service.longitude) {
			const marker = new google.maps.Marker({
				position: { lat: service.latitude, lng: service.longitude },
				map: map,
				title: service.name,
			});
			// Optional: add info window
			const infoWindow = new google.maps.InfoWindow({
				content: `<h5>${service.name}</h5><p>${service.location}</p>`,
			});
			marker.addListener("click", () => {
				infoWindow.open(map, marker);
			});
			markers.push(marker);
		}
	});
}

// This file can include interactive features or future upgrades

document.addEventListener("DOMContentLoaded", function () {
	// Add smooth scroll to all anchor links
	document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
		anchor.addEventListener("click", function (e) {
			e.preventDefault();
			document.querySelector(this.getAttribute("href")).scrollIntoView({
				behavior: "smooth",
			});
		});
	});
	if (typeof google !== "undefined" && google.maps) {
		initMap();
	} else {
		// If not loaded yet, retry after a short delay
		setTimeout(initMap, 500);
	}
});
