<div align="center">
  <img src="https://raw.githubusercontent.com/trivikram-s/django-spotify-clone/main/static/img/SoulPlayer-Logo.png" alt="SoulPlayer Logo" width="200"/>
</div>

<h1 align="center">SoulPlayer</h1>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#core-features">Features Deep-Dive</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <b>A premium, feature-rich music streaming web application built with Django and Tailwind CSS.</b>
</p>

---

## 📖 Overview

SoulPlayer is a modern, high-performance web-based music streaming platform designed with a focus on premium aesthetics and intelligent features. Developed primarily with the Django framework and styled rapidly using Tailwind CSS, SoulPlayer brings desktop-class media streaming experiences to the browser. 

Beyond standard playback functionality, the platform differentiates itself with advanced features like **Natural Language Voice Search (NLP)** and **Dynamic Background Play Tracking**.

---

## 🏗️ Architecture & System Design

SoulPlayer follows a classic **Model-View-Template (MVT)** architecture utilized by Django, augmented with vanilla JavaScript for asynchronous frontend operations (AJAX) to maintain a seamless, single-page-application feel during media playback.

<details>
<summary><b>Click to expand Architectural Flow</b></summary>

1. **Client Layer (The Browser):** Renders the UI using HTML rendered by Django Templates and Tailwind CSS for styling. Global event listeners capture media playback actions.
2. **Asynchronous Handlers (Vanilla JS `fetch` APIs):** When a user plays a song, the global `audio` element begins streaming the buffer. Simultaneously, an invisible `/record_play/<id>/` POST request is fired to the backend, complete with explicit CSRF token verification, to track user listening history.
3. **Routing Layer (`music/urls.py`):** Django’s URL dispatcher routes incoming REST-like endpoints and standard GET requests to the appropriate controller views.
4. **Controller Layer (`music/views.py`):** Handles the core business logic. 
    - Queries the database via the Django ORM.
    - Processes Natural Language queries through the `spaCy` NLP engine.
    - Makes external calls to the Google/YouTube Data API for podcast ingestion.
5. **Data Layer (`models.py` & SQLite Database):** Stores the relational mapping of Users, UserProfiles (1-to-1 User mapping), Artists, Songs, and Playlists (Many-to-Many relationships mapping songs to playlists and users).
</details>

---

## 🌟 Core Features Deep-Dive

### 1. Natural Language Voice Search (NLP)
Instead of forcing users to explicitly filter by artist or genre, SoulPlayer integrates **spaCy**, an industry-level Natural Language Processing library.
* **How it works:** When a user searches *"play some romantic arijit singh songs"*, the NLP pipeline intercepts the query. It categorizes grammatical tokens, actively stripping out stop words (*"some", "songs", "play"*) to isolate target keywords. It then routes the request intelligently—if it finds an exact song match, it auto-plays it. If it finds an artist match, it redirects to the Artist Portfolio.

### 2. Premium Music Player & State Management
The project features a sleek, global bottom-bar player and a dedicated Full-Screen View (`/play_song/<id>`).
* **Design:** Utilizes modern "Glassmorphism" paradigms (blur backdrops, semi-transparent gradients, glowing accents).
* **DOM APIs:** Interacts deeply with the HTML5 `<audio>` API to calculate track duration, current timestamp precision, and smooth slider tracking.

### 3. Background Sync & User Profiles
We utilize Django Signals (`post_save`) to automatically attach an extended `UserProfile` model to every new user registration.
* **History Tracking:** JavaScript asynchronous `fetch` requests bypass the need for full page reloads. As users listen to tracks, their `played_songs` Many-To-Many relationship is updated silently in the background.
* **Dashboard:** Users have a dedicated customizable Profile page to view their listening history and favorite artist collections.

### 4. YouTube Podcast Integration
SoulPlayer isn't just limited to local database music. It uses the `requests` library to interface with the **YouTube Data API v3**. It dynamically queries YouTube for high-quality music podcasts, parses the incoming JSON, and renders fully playable media cards directly within the SoulPlayer UI.

---

## 🛠️ Tech Stack

### Backend
*   **Framework:** Django 5.x (Python)
*   **Database:** SQLite (Development & Free Tier Production ready)
*   **NLP Engine:** spaCy (`en_core_web_sm`)
*   **API Interactions:** Python `requests` module

### Frontend
*   **Templating:** Django Template Engine
*   **Styling:** Tailwind CSS (via CDN)
*   **Interactivity:** Vanilla JS (ES6) 
*   **Icons:** FontAwesome 6

---

## 🚀 Installation & Local Setup

To run SoulPlayer locally on your machine, follow these steps:

### 1. Clone the repository
```bash
git clone https://github.com/rudra00434/SoulPlayer.git
cd SoulPlayer
cd SPOTIFY
```

### 2. Create a virtual environment (Recommended)
```bash
python -m venv venv

# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download the spaCy NLP Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Environment Variables Configuration
Create a file named `.env` in the same directory as `manage.py`.
```env
# Required for Podcast fetching module:
YOUTUBE_API_KEY=your_google_api_key_here
```

### 6. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Initialize Admin Account
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`. You can log into the admin panel at `http://127.0.0.1:8000/admin/` to add Artists, Songs, and Categories manually.

---

## ☁️ Deployment Architecture (Render)

SoulPlayer utilizes a custom deployment flow designed specifically for PaaS providers like **Render.com**.

The application uses an automated `build.sh` script to handle production environments. Instead of manually SSHing into the server to install dependencies, the script:
1. Installs Python packages via `pip`.
2. Downloads the heavy `spaCy` NLP model binaries to the production server.
3. Automatically maps static assets via `collectstatic` for the `Whitenoise` middleware to serve.
4. Executes zero-downtime Django database migrations via `migrate`.

**Infrastructure Details:**
* **WSGI Server:** Gunicorn
* **Static File Serving:** Whitenoise (Configured in `settings.py`)

> ⚠️ **Limitation Warning:** If utilizing ephemeral free-tier instances (like Render Free Web Services), local media assets (User uploaded MP3s and JPGs located in `/media/`) will be purged upon container sleep. A permanent production scale-up requires migrating the `DEFAULT_FILE_STORAGE` to an **AWS S3** bucket or **Cloudinary**.

---

## 🤝 Contributing

Contributions, issues, and feature requests are highly encouraged! If you have suggestions for improving the UI, optimizing database queries, or adding new APIs, feel free to check the [issues page](https://github.com/rudra00434/SoulPlayer/issues) or submit a Pull Request.

---

## 📝 License

This project is open-source and available under the MIT License.
