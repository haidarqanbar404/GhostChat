# GhostChat - AI-Powered Stealth Messenger

**GhostChat** is a secure, steganographic messaging tool that uses **Telegram** as a transport layer. It hides end-to-end encrypted messages inside natural-looking, AI-generated cover text (using Local LLMs via Ollama), making your sensitive conversations indistinguishable from casual chats.

## Features

* **End-to-End Encryption:** Messages are encrypted using AES (Fernet) before leaving your device.
* **AI Steganography:** Uses **Ollama (Local LLM)** to wrap encrypted payloads in natural Syrian dialect conversations. To an observer, it looks like a normal chat like "كيفك؟" or "وينك؟".
* **Telegram Transport:** Uses the Telegram API (Telethon) to send and receive messages, bypassing the need for custom servers.
* **Local & Private:** No external AI APIs (Google/OpenAI) are used. Everything runs locally on your machine for maximum privacy.
* **Modern GUI:** Built with `CustomTkinter` for a sleek, dark-mode interface.
* **Zero-Metadata:** No metadata is stored on cloud servers; only the encrypted payload travels through Telegram.

## Tech Stack

* **Language:** Python 3.10+
* **GUI:** CustomTkinter
* **Network:** Telethon (Telegram Client API)
* **Database:** SQLite + SQLAlchemy
* **AI Engine:** Ollama (running Qwen 2.5 or Llama 3)
* **Cryptography:** `cryptography` library (Fernet)

## Prerequisites

Before running the application, ensure you have the following:

1.  **Python 3.10** or higher.
2.  **Ollama** installed and running.
    * Pull the model: `ollama run qwen2.5:0.5b`
3.  **Telegram API Credentials:**
    * Get your `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/haidarqanbar404/GhostChat.git
    cd GhostChat
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add:
    ```ini
    TG_API_ID=your_api_id_here
    TG_API_HASH=your_api_hash_here
    OLLAMA_MODEL=qwen2.5:0.5b
    ```

## Usage

1.  Make sure **Ollama** is running in the background.
2.  Run the application:
    ```bash
    python gui_app.py
    ```
3.  **First Login:** Enter your phone number to authenticate with Telegram.
4.  **Add Contact:**
    * Click `+ New Contact`.
    * Enter the Telegram username of your friend (who must also use GhostChat).
    * **Important:** Exchange the `Secret Key` securely (offline or via Signal). Both parties must have the same key.
5.  **Chat:** Type your message and hit send. The app will generate a cover text automatically.

## Security Note

* This tool is intended for educational purposes and privacy research.
* The `.session` file generated contains your Telegram access token. **NEVER share this file.**
* Ensure your `.env` file is included in `.gitignore`.

## License

Distributed under the MIT License. See `LICENSE` for more information.
