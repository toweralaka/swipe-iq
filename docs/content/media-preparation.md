# Prepare lightweight media

| Kind | Accepted local formats | Maximum size | Required alternatives/metadata |
| --- | --- | --- | --- |
| Image | PNG, JPEG | 250,000 bytes | Meaningful alternative text; attribution/rights |
| Audio | MP3, WAV | 1,000,000 bytes, 90 seconds | Transcript, verified duration; attribution/rights |
| Video | MP4 | 5,000,000 bytes, 60 seconds, height ≤480 pixels | Transcript/text alternative, WEBVTT captions, verified duration/height; attribution/rights |

Limits use decimal bytes (KB/MB). Use short manually prepared files; video should be exported with Android-compatible H.264/AAC and fast-start playback where your editor supports it. Prefer MP3 for small narration; long WAV files often exceed the cap.

Use a media editor/player to inspect duration and dimensions. ffprobe may be used if already available, but is not a required project dependency. Export compressed versions before upload; no automatic transcoding or adaptive streaming is implemented.

Automatic validation checks extension, basic file signature, nonempty size, and declared metadata limits. It does not fully decode files, prove codecs/playback, measure real audio/video duration/resolution, or verify caption timing. The reviewer must perform these checks and confirm metadata. Header checks are not malware scanning; uploads are staff-only, not an unrestricted public upload facility.

Video captions are stored as checked WEBVTT text. Include timestamps and the spoken educational content. Audio requires a transcript; images require alt text. Cards also require an explanation/summary that works without loading media.

Files are stored under backend/private_media/, ignored by Git. Django admin file links use the permission-protected editorial preview endpoint. No public /media/ or /private-media/ serving is configured, including DEBUG mode. Later student APIs must authorize media delivery and expose published content only; do not add a public media route as a shortcut.

Use the admin preview to inspect files. Preview responses are private/no-store. Deleting database drafts does not provide file garbage collection; retain files until an explicit safe cleanup/backup policy is designed. Back up local uploads separately when needed.

Mobile tap-to-play, caching, data saver, and on-screen captions are Milestone 4 work; this milestone prepares the reviewed assets and metadata.
