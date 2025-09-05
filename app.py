import base64
import io
import os
from typing import List
import requests
import streamlit as st
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip
from moviepy.audio.AudioClip import AudioClip
from PIL import Image
import numpy as np
import tempfile
import random

APP_TITLE = "AI 1‑Minute Video Generator (SD + TTS)"
DEFAULT_SD_URL = os.getenv("SD_API_URL", "http://127.0.0.1:7860")

st.set_page_config(page_title=APP_TITLE, page_icon="🎬", layout="centered")

st.title(APP_TITLE)
st.caption("Enter your narration script and a background image prompt. The app will generate a 60‑second video without text overlays.")

with st.expander("Backend Settings", expanded=False):
    sd_url = st.text_input("Stable Diffusion WebUI API URL", value=DEFAULT_SD_URL, help="For Automatic1111 WebUI typically http://127.0.0.1:7860")
    steps = st.slider("SD Steps", 10, 50, 25)
    cfg_scale = st.slider("CFG Scale", 1.0, 15.0, 7.0)
    width = st.select_slider("Image Width", options=[512, 576, 640, 704, 720], value=720)
    height = st.select_slider("Image Height", options=[768, 960, 1024, 1152, 1280], value=1280)
    num_images = st.slider("Number of background images", 1, 8, 4, help="Images will be cut into equal segments to make up 60 seconds.")
    sampler = st.text_input("Sampler name (optional)", value="Euler a")

script = st.text_area("Narration Script", height=150, placeholder="Type your narration here...")
bg_prompt = st.text_area("Background Prompt (for SD)", height=120, placeholder="e.g., 'epic cinematic forest at dawn, volumetric light, ultra-detailed, 8k'")
neg_prompt = st.text_input("Negative Prompt (optional)", value="nsfw, lowres, blurry, deformed, watermark, text, logo")

col1, col2 = st.columns(2)
voice_lang = col1.text_input("Voice language (gTTS code)", value="en", help="e.g., en, hi, ta")
voice_slow = col2.checkbox("Slow voice", value=False)

gen_btn = st.button("🚀 Generate 1‑Minute Video")

def sd_txt2img(sd_base_url: str, prompt: str, negative_prompt: str, steps: int, cfg_scale: float,
               width: int, height: int, num_images: int, sampler_name: str = None) -> List[Image.Image]:
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "batch_size": 1,
        "n_iter": num_images,
        "restore_faces": False,
        "tiling": False
    }
    if sampler_name:
        payload["sampler_name"] = sampler_name

    url = sd_base_url.rstrip("/") + "/sdapi/v1/txt2img"
    resp = requests.post(url, json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()
    imgs = []
    for b64img in data.get("images", []):
        img_bytes = base64.b64decode(b64img.split(",", 1)[-1])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        imgs.append(img)
    return imgs

def ken_burns_clip(img: Image.Image, duration: float, final_size=(720, 1280)) -> ImageClip:
    # Convert PIL to numpy
    arr = np.array(img)
    clip = ImageClip(arr).set_duration(duration)

    # Slight zoom/pan to add life
    # Random start/end zoom factors
    z1 = 1.0
    z2 = 1.08 + random.random()*0.06  # 1.08 .. 1.14
    w, h = clip.size
    fw, fh = final_size

    def make_frame(t):
        # progress 0..1
        p = t/duration if duration > 0 else 0
        z = z1*(1-p) + z2*p
        # Zoom by resizing original frame
        zw, zh = int(w*z), int(h*z)
        resized = Image.fromarray(arr).resize((zw, zh), Image.LANCZOS)
        # Center crop to final size
        left = max(0, (zw - fw)//2)
        top = max(0, (zh - fh)//2)
        crop = resized.crop((left, top, left+fw, top+fh))
        return np.array(crop)

    kb = clip.set_make_frame(make_frame)
    kb = kb.resize(final_size)
    return kb

def silence_clip(duration: float, fps: int = 44100) -> AudioClip:
    return AudioClip(lambda t: 0*t, duration=duration, fps=fps)

if gen_btn:
    if not script.strip():
        st.error("Please enter a narration script.")
        st.stop()
    if not bg_prompt.strip():
        st.error("Please enter a background prompt for Stable Diffusion.")
        st.stop()
    try:
        with st.spinner("Generating background images with Stable Diffusion..."):
            imgs = sd_txt2img(sd_url, bg_prompt, neg_prompt, steps, cfg_scale, width, height, num_images, sampler_name=sampler if sampler else None)
            if not imgs:
                st.error("Stable Diffusion returned no images. Check your SD WebUI server and settings.")
                st.stop()

        seg_duration = 60.0 / len(imgs)

        with st.spinner("Creating narration (gTTS)..."):
            tts = gTTS(script, lang=voice_lang, slow=voice_slow)
            tmpdir = tempfile.mkdtemp()
            tts_path = os.path.join(tmpdir, "narration.mp3")
            tts.save(tts_path)

        narration = AudioFileClip(tts_path)
        # Build image sequence with Ken Burns effect
        with st.spinner("Stitching video..."):
            clips = [ken_burns_clip(img, seg_duration, final_size=(width, height)) for img in imgs]
            vclip = concatenate_videoclips(clips, method="compose")

            # Handle audio to enforce exactly 60s
            if narration.duration >= 60.0:
                aclip = narration.subclip(0, 60.0)
            else:
                pad = silence_clip(60.0 - narration.duration)
                aclip = CompositeAudioClip([narration.set_start(0), pad.set_start(narration.duration)])

            vclip = vclip.set_duration(60.0).set_audio(aclip)

            out_path = os.path.join(tmpdir, "ai_video_60s.mp4")
            vclip.write_videofile(out_path, fps=24, audio_codec="aac", codec="libx264", threads=4, verbose=False, logger=None)

        st.success("Done! Your 1‑minute video is ready.")
        with open(out_path, "rb") as f:
            st.download_button("⬇️ Download 60s Video", data=f.read(), file_name="ai_video_60s.mp4", mime="video/mp4")

        # Preview first generated image
        st.subheader("Preview (first background image)")
        st.image(imgs[0], use_column_width=True, caption="Generated by SD")

    except requests.exceptions.RequestException as e:
        st.error(f"Stable Diffusion API error: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.exception(e)