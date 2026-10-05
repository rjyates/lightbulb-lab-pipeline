"""Kip's voice via the ElevenLabs API, with character-level timestamps for exact caption/scene timing."""
import base64, json, os, time
import requests

API = 'https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps'

def synthesize(text, cfg, out_mp3, out_json):
    key, voice = cfg.get('ELEVENLABS_API_KEY'), cfg.get('ELEVENLABS_VOICE_ID')
    if not key or not voice:
        raise RuntimeError('Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in config.env')
    body = {'text': text, 'model_id': cfg['ELEVENLABS_MODEL_ID'],
            'voice_settings': {'stability': float(cfg['ELEVENLABS_STABILITY']), 'similarity_boost': float(cfg['ELEVENLABS_SIMILARITY']),
                               'speed': float(cfg['ELEVENLABS_SPEED'])}}
    for attempt in range(3):
        r = requests.post(API.format(voice=voice), params={'output_format': 'mp3_44100_128'},
                          headers={'xi-api-key': key, 'Content-Type': 'application/json'}, json=body, timeout=300)
        if r.status_code == 200: break
        if r.status_code in (429, 500, 502, 503) and attempt < 2: time.sleep(20 * (attempt + 1)); continue
        raise RuntimeError(f'ElevenLabs error {r.status_code}: {r.text[:400]}')
    data = r.json()
    with open(out_mp3, 'wb') as f: f.write(base64.b64decode(data['audio_base64']))
    al = data.get('normalized_alignment') if not data.get('alignment') else data['alignment']
    json.dump({'text': text, 'alignment': al}, open(out_json, 'w'))
    return out_mp3, out_json

def characters_left(cfg):
    """free-tier budget check (returns None if unknown)"""
    try:
        r = requests.get('https://api.elevenlabs.io/v1/user/subscription', headers={'xi-api-key': cfg['ELEVENLABS_API_KEY']}, timeout=30)
        d = r.json(); return d['character_limit'] - d['character_count']
    except Exception:
        return None
