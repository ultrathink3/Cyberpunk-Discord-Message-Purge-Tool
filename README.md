🏙️ Neurowipe
Cyberpunk Discord Message Purge Tool — Erase Your Digital Trace
<img width="530" height="479" alt="image" src="https://github.com/user-attachments/assets/30fec857-1d7d-4e02-9a7e-decebf6d20d2" />

License: MIT Python: 3.10+

Neurowipe is a high-performance, aesthetically pleasing Discord message deletion tool designed for the digital ghost. In an age of permanent records, Neurowipe provides the interface to scrub your history across guilds and DMs with precision and style.

App Icon

⚡ Features
Profile Management: Securely store multiple Discord accounts using OS-level encryption (Keyring) or local Fernet fallback.
Deep Search: Filter messages by keyword, date range, regex, or attachment type across entire guilds or specific channels.
Smart Rate Limiting: Advanced adaptive rate-limiter designed to mimic human behavior and avoid Discord's automated detection.
Data Analytics: Visualize your activity with heatmaps, timelines, and server distribution charts before you wipe it.
Scheduled Deletion: Set up recurring purge tasks to keep your digital footprint minimal.
Cyberpunk UI: A neon-drenched, high-contrast interface built with PySide6.
🛠️ Installation
Prerequisites
Python 3.10 or higher
A Discord User Token (Use with caution; self-bots are against Discord ToS)
Setup
Clone the repository:

git clone https://github.com/yourusername/neurowipe.git
cd neurowipe
Create a virtual environment:

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
Install dependencies:

pip install -e .
🚀 Usage
Run the application:

neurowipe
Enter your Discord Token or select a saved profile.
Scan Servers/DMs: Let Neurowipe index your message history.
Filter: Use the Purge view to select exactly what needs to be erased.
Execute: Watch the digital rain as your traces disappear.
🛡️ Security
Neurowipe takes your privacy seriously:

Tokens are never sent to any third-party server except Discord's official API.
Local storage is encrypted using the best available method for your OS.
No telemetry or tracking.
⚖️ Disclaimer
Using self-bots or automated tools on user accounts is a violation of Discord's Terms of Service and can lead to account termination. Neurowipe is provided for educational and personal data management purposes only. Use at your own risk.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
