"""YouTube Data API: one-time sign-in + private (draft) uploads.

Note: until your Google Cloud project passes YouTube's API audit, every API upload is locked
to private and can't be made public. Leave YOUTUBE_UPLOAD=false until the audit is approved;
the pipeline then leaves a ready-to-upload folder instead.
"""
import os, sys
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']

def _creds(cfg, interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    tok = cfg['YOUTUBE_TOKEN']; creds = None
    if os.path.exists(tok): creds = Credentials.from_authorized_user_file(tok, SCOPES)
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    if not creds or not creds.valid:
        if not interactive: raise RuntimeError('No YouTube sign-in yet. Run: python3 -m lightbulb.youtube auth')
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(cfg['YOUTUBE_CLIENT_SECRET'], SCOPES)
        creds = flow.run_local_server(port=8765, open_browser=False)
    os.makedirs(os.path.dirname(tok), exist_ok=True); open(tok, 'w').write(creds.to_json()); return creds

def client(cfg, interactive=False):
    from googleapiclient.discovery import build
    return build('youtube', 'v3', credentials=_creds(cfg, interactive), cache_discovery=False)

def upload(cfg, path, title, description, tags, privacy='private', category='27', thumbnail=None, playlist_id=None, publish_at=None):
    from googleapiclient.http import MediaFileUpload
    yt = client(cfg)
    status = {'privacyStatus': privacy, 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': False}
    if publish_at: status.update({'privacyStatus': 'private', 'publishAt': publish_at})
    body = {'snippet': {'title': title[:100], 'description': description[:5000], 'tags': tags[:30], 'categoryId': category,
                        'defaultLanguage': 'en', 'defaultAudioLanguage': 'en'}, 'status': status}
    req = yt.videos().insert(part='snippet,status', body=body, media_body=MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None: _, resp = req.next_chunk()
    vid = resp['id']
    if thumbnail:
        try: yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumbnail)).execute()
        except Exception as e: print('thumbnail not set (phone-verify the channel to allow custom thumbnails):', e)
    if playlist_id:
        yt.playlistItems().insert(part='snippet', body={'snippet': {'playlistId': playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}}).execute()
    return vid

if __name__ == '__main__':
    from .config import load
    if len(sys.argv) > 1 and sys.argv[1] == 'auth':
        print('A sign-in link will appear. If this server has no browser, run on your laptop first:\n'
              '  ssh -L 8765:localhost:8765 you@server   (then open the link on your laptop)')
        client(load(), interactive=True); print('Signed in. Token saved to', load()['YOUTUBE_TOKEN'])
    elif len(sys.argv) > 1 and sys.argv[1] == 'playlists':
        yt = client(load())
        for p in yt.playlists().list(part='snippet', mine=True, maxResults=50).execute().get('items', []): print(p['id'], p['snippet']['title'])
