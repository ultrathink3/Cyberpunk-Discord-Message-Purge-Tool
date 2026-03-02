# 🏙️ Neurowipe

**Cyberpunk Discord Message Purge Tool — Erase Your Digital Trace**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

Neurowipe is a high-performance, aesthetically pleasing Discord message deletion tool designed for the digital ghost. In an age of permanent records, Neurowipe provides the interface to scrub your history across guilds and DMs with precision and style.

![App Icon](src/neurowipe/resources/icons/app_icon.jpg)

## ⚡ Features

- **Profile Management**: Securely store multiple Discord accounts using OS-level encryption (Keyring) or local Fernet fallback.
- **Deep Search**: Filter messages by keyword, date range, regex, or attachment type across entire guilds or specific channels.
- **Smart Rate Limiting**: Advanced adaptive rate-limiter designed to mimic human behavior and avoid Discord's automated detection.
- **Data Analytics**: Visualize your activity with heatmaps, timelines, and server distribution charts before you wipe it.
- **Scheduled Deletion**: Set up recurring purge tasks to keep your digital footprint minimal.
- **Cyberpunk UI**: A neon-drenched, high-contrast interface built with PySide6.

## 🛠️ Installation

### Prerequisites
- Python 3.10 or higher
- A Discord User Token (Use with caution; self-bots are against Discord ToS)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/neurowipe.git
   cd neurowipe
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

## 🚀 Usage

Run the application:
```bash
neurowipe
```

1. **Enter your Discord Token** or select a saved profile.
2. **Scan Servers/DMs**: Let Neurowipe index your message history.
3. **Filter**: Use the Purge view to select exactly what needs to be erased.
4. **Execute**: Watch the digital rain as your traces disappear.

## 🛡️ Security

Neurowipe takes your privacy seriously:
- **Tokens are never sent to any third-party server** except Discord's official API.
- **Local storage is encrypted** using the best available method for your OS.
- **No telemetry or tracking**.

## ⚖️ Disclaimer

**Using self-bots or automated tools on user accounts is a violation of Discord's Terms of Service and can lead to account termination.** Neurowipe is provided for educational and personal data management purposes only. Use at your own risk.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
