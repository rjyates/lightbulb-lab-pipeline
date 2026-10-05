"""Free phone notifications through ntfy.sh (install the ntfy app and subscribe to your topic)."""
import requests

def send(cfg, title, message, url=None, priority='default'):
    topic = cfg.get('NTFY_TOPIC')
    if not topic: print(f'[notify] {title}: {message}'); return
    headers = {'Title': title.encode('utf-8'), 'Priority': priority, 'Tags': 'bulb'}
    if url: headers['Click'] = url
    try: requests.post(f"{cfg.get('NTFY_SERVER', 'https://ntfy.sh').rstrip('/')}/{topic}", data=message.encode('utf-8'), headers=headers, timeout=20)
    except Exception as e: print('[notify] failed:', e)
