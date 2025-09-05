# AI 1‑Minute Video Generator (Stable Diffusion + gTTS + MoviePy)

Create a 60‑second video from your **script** and a **background prompt**.
- No text overlays
- Uses **Stable Diffusion WebUI (Automatic1111)** for background images via API
- Uses **gTTS** for narration
- Uses **MoviePy** to stitch video

## 1) Prerequisites (Free/Local)
- Python 3.10+
- `ffmpeg` installed and in PATH
- Stable Diffusion WebUI (Automatic1111) running locally with API enabled  
  Start A1111 with `--api` flag. The default URL is `http://127.0.0.1:7860`

## 2) Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 3) Run the app
```bash
# Ensure A1111 is running with --api
export SD_API_URL="http://127.0.0.1:7860"   # optional; you can also set it in the UI
streamlit run app.py
```

Open the local URL Streamlit shows (usually http://localhost:8501).  
Enter your **narration** and **background prompt** → click **Generate** → download the MP4.

## 4) Make It an Android App (Free)
**Option A — Wrap the web app**
1. Deploy this Streamlit app for free (e.g., any free Python hosting that allows Streamlit; or run on your own PC and expose via a free tunnel like `ngrok`).
2. Turn the site into a **PWA** (Streamlit apps work decently as installable web apps).
3. Use any free **PWA‑to‑APK** wrapper tool (open‑source or online). These tools package your PWA URL into a WebView‑based APK.
4. Install the APK on your phone.
> Pros: simplest; Cons: requires internet to reach your server if not on the same network.

**Option B — Native Android with WebView (Offline wrapper)**
1. Create a minimal Android project (Android Studio) with a single WebView Activity.
2. Point the WebView to your locally hosted Streamlit app URL on the device (or LAN IP). You can bundle a local page that fetches from `http://127.0.0.1:8501` if you run Streamlit on‑device.
3. Build the APK.  
> Pros: free; Cons: more setup; Streamlit on Android is not officially supported—better to host elsewhere.

**Option C — Kivy/Buildozer (Full native)**
Re‑implement a simple UI in **Kivy** calling the same SD WebUI API and using **gTTS**/**MoviePy**. Then build a free APK with **Buildozer** on Linux.  
> Pros: offline capable; Cons: more dev work.

## 5) Notes
- The app always outputs exactly **60 seconds**. If narration is shorter, it pads with silence. If longer, it trims to 60s.
- You can change image size, number of images, steps, sampler in the **Backend Settings** panel.
- For Hindi/Malayalam/etc voices, change the `Voice language` to the relevant **gTTS code** (e.g., `hi`, `ml`).

## 6) Troubleshooting
- **No images returned**: Ensure A1111 is running with `--api` and try a different sampler.
- **ffmpeg missing**: Install ffmpeg and ensure `ffmpeg -version` works in your terminal.
- **Heroku/Streamlit Cloud**: Some hosts disallow background processing or have time limits—keep prompts light (<=4 images, 720x1280).

---

Enjoy!