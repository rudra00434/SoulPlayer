<div align="center">
  <img src="https://raw.githubusercontent.com/trivikram-s/django-spotify-clone/main/static/img/SoulPlayer-Logo.png" alt="SoulPlayer Logo" width="200"/>
</div>

<h1 align="center">SoulPlayer</h1>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#license">License</a>
</p>

<p align="center">
  <b>A premium, feature-rich music streaming web application built with Django and Tailwind CSS.</b>
</p>

---

## ✨ Features

SoulPlayer offers a stunning, modern dark-themed user interface inspired by the best music streaming platforms, packed with powerful features:

*   🎵 **Premium Music Player:** Play, pause, seek, and control volume with a sleek bottom player or a dedicated full-screen view.
*   🎧 **Smart Song Library:** Browse songs, artists, and playlists with beautiful glassmorphism UI elements.
*   🤖 **NLP Voice Search:** Find songs intelligently using natural language processing (spaCy) queries (e.g., "play some romantic arijit singh songs").
*   🎙️ **YouTube Podcast Integration:** Fetch and display external music podcasts seamlessly using the YouTube Data API.
*   👤 **Dynamic User Profiles:** Track listening history automatically and manage favorite artists from a dedicated, premium profile page.
*   💾 **Playlists & Favorites:** Create custom playlists and save favorite tracks and artists for easy access.
*   📱 **Fully Responsive:** Perfectly optimized for mobile, tablet, and desktop viewing.

---

## 🛠️ Tech Stack

### Backend
*   **Framework:** Django 5.x (Python)
*   **Database:** SQLite (Development & Free Tier Production)
*   **NLP Engine:** spaCy (`en_core_web_sm`)

### Frontend
*   **Styling:** Tailwind CSS (via CDN for rapid styling)
*   **JavaScript:** Vanilla JS (DOM manipulation, AJAX fetches for background tracking)
*   **Icons:** FontAwesome
*   **UI Paradigm:** Glassmorphism, dynamic gradients, deep dark mode.

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

### 5. Add your Environment Variables
Create a file named `.env` in the same directory as `manage.py` (or set them in your terminal) and add your YouTube API Key if you want podcasts to work:
```env
# Optional but recommended for podcasts:
YOUTUBE_API_KEY=your_google_api_key_here
```

### 6. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`. You can log into the admin panel at `http://127.0.0.1:8000/admin/` to add Artists and Songs manually.

---

## ☁️ Deployment (Render)

This project is currently configured to be easily deployed on **Render** using a custom `build.sh` script.

1.  Connect your GitHub repository to Render as a **Web Service**.
2.  Set the **Build Command** to:
    ```bash
    ./build.sh
    ```
3.  Set the **Start Command** to:
    ```bash
    gunicorn mysite.wsgi:application
    ```
4.  Add your environment variables (like `YOUTUBE_API_KEY`) in the Render dashboard.

> **Note on Media Files:** If you are using Render's Free Tier, user-uploaded media files (like album art and `.mp3` files uploaded through the admin panel) are stored in the ephemeral file system and will be wiped when the server goes to sleep. To keep music permanent on production, consider migrating media storage to **Cloudinary** or **AWS S3**.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/rudra00434/SoulPlayer/issues).

---

## 📝 License

This project is open-source and available under the MIT License.
