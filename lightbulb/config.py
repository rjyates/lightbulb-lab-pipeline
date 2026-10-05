"""Settings come from config.env in the repo root (copy config.example.env). Never commit config.env."""
import os
from .core import ROOT

def load():
    cfg = {}
    path = os.path.join(ROOT, 'config.env')
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1); cfg[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in os.environ.items():
        if k.startswith(('ELEVENLABS_', 'YOUTUBE_', 'NTFY_', 'LBL_')): cfg[k] = v
    cfg.setdefault('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2')
    cfg.setdefault('ELEVENLABS_STABILITY', '0.5'); cfg.setdefault('ELEVENLABS_SIMILARITY', '0.75'); cfg.setdefault('ELEVENLABS_SPEED', '1.0')
    cfg.setdefault('YOUTUBE_UPLOAD', 'false'); cfg.setdefault('YOUTUBE_PRIVACY', 'private')
    cfg.setdefault('YOUTUBE_CLIENT_SECRET', os.path.join(ROOT, 'secrets', 'client_secret.json'))
    cfg.setdefault('YOUTUBE_TOKEN', os.path.join(ROOT, 'secrets', 'youtube_token.json'))
    cfg.setdefault('LBL_OUTPUT', os.path.join(ROOT, 'output'))
    cfg.setdefault('LBL_WORKERS', str(max(1, (os.cpu_count() or 2))))
    return cfg

def truthy(v): return str(v).lower() in ('1', 'true', 'yes', 'on')
