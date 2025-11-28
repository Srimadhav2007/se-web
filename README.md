      Panchangopedia

A website which can be used to convert the time we use today (hours, minutes and days or the Gregorian calendar) into the hindu time periods.
Using Swiss Ephemeris / Skyfield-grade calculations, ensuring high accuracy.

1. Uniqueness of Panchangopedia
Panchangopedia is not just another Panchang-display app. Its uniqueness comes from the following pillars:

a) Real Astronomical Computation
We compute Panchang elements (tithi, nakshatra, yoga, karana, masa, sunrise, sunset, muhurthas, etc.) using Swiss Ephemeris / Skyfield-grade calculations, ensuring high accuracy.
This makes the platform data-scientific and transparent, unlike static or horoscope-driven apps.

b) Dynamic Location Awareness
Panchang is entirely location-dependent.
Panchangopedia auto-detects:
•	Latitude & longitude from device GPS
•	Timezone using tz-lookup
•	Elevation using online elevation APIs
This results in precise sunrise, sunset, and muhurtas for any location globally.

c) Hindu Time System (Kala) Visualization
A rare and innovative feature:
A live, animated panel showing:
•	Ghaṭi
•	Muhūrta
•	Vinādi
•	Prāṇa
•	Seconds since sunrise
•	Real-time Hindu clock progression
This brings ancient Hindu timekeeping into a modern digital UI — something almost no app currently offers.

d) Modular Panchang Engine
The backend is architected so that:
•	Calculation logic is in drik.py
•	Views remain lightweight
This modularity makes Panchangopedia extensible and academically valuable.

e) Transparent + Educational
Panchangopedia explains:
•	How Tithi is computed (Moon–Sun angular difference)
•	How Nakshatra is derived (Moon’s ecliptic longitude)
•	How Yoga is computed (sum of longitudes)
•	How Karana is half-tithi
•	How Muhurtas are derived from sunrise-to-sunset day division
This promotes cultural literacy backed by astronomical correctness.

2. Features Implemented in Release-1

1. Panchang Computation Engine
•	Computes Tithi, Nakshatra, Yoga, Karana, Rashi (Moon)
•	Computes Sunrise, Sunset (local time, location-sensitive)
•	Computes current-moment Panchang (instant snapshot)
•	Computes day-by-sunrise Panchang (traditional method)

2. Full-Moon (Purnima) Calculations
•	Next full moon time (UTC + Local)
•	Nakshatra at full moon
•	Lunar month (Masa)

3. Hindu Kala Clock (Live Panel)
A floating side-panel that shows:
•	Live ticking clock
•	Seconds since sunrise
•	Ghaṭi count + breakdown
•	Muhūrta count
•	Vinādi and Prāṇa values
•	Automatically syncs with the backend sunrise time
This component gives Panchangopedia a signature feature.

3. Smart Location Detection

•	GPS-based current location selection
•	Auto-detected timezone
•	Auto-detected elevation from map/Elevation API
•	Preset Indian cities for quick access

4. Modern UI / UX

•	Vite + React frontend
•	Responsive layout
•	Smooth transitions
•	Distinct “ancient theme” UI
•	Cards for each Panchang component
•	Side-panel that slides in/out cleanly

5. Backend Architecture

•	Django backend
•	Separate logic file (drik.py) — clean architecture
•	JSON API for frontend integration
 

6Planet position calculator : 

We have made it so that we calculate the postion of the b=planets based on the date and time.
We showed the positions of all of them respect to other planets, we also calculated 
-> Rashi
-> Nakshatra 
-> lonitudes

In the sky view we calculated 
-> Angle 
-> Longitude 
-> Altitude.

The video link to our project is here : 

[Click to watch video](SE_web_video.mp4)

The screenshots from our project are : 





Contributions: 

SriMadhav : Has given the idea for the UI and helped in making it. Helped in joining all these together.

Bhargav : Has helped in making the elements more granulated.

Varshith : Has helped in calculations and helped in making UI.

Rudresh : Has made the feature which can view the allignment of the plantes.

Anil : Helped in making the UI look better.
