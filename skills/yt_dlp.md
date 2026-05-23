---
name: YouTube Downloader (yt-dlp)
type: tool
execution: stateful
description: Downloads videos, playlists, or extracts audio from YouTube and other sites using yt-dlp.
---

## Purpose
Integrate `yt-dlp` command-line utility into the SOVRN orchestration stack, enabling Hermes to download video/audio research, references, podcast clips, and digital assets.

## Parameters
- `url` (string, required): The target YouTube video or playlist URL.
- `mode` (string, optional): One of `video` (default) or `audio`.
- `format` (string, optional): E.g., `mp3`, `mp4`, `best`. Defaults to `best`.
- `output_dir` (string, optional): Output folder. Defaults to `~/Downloads/`.
- `playlist` (boolean, optional): Whether to download whole playlists if URL targets one. Defaults to `false`.
- `embed_metadata` (boolean, optional): Embed original video metadata, subtitles, and thumbnail. Defaults to `true`.

## Steps
1. **[--dry-run gate]** Show:
   - Target URL: `[url]`
   - Operation Mode: `[mode]`
   - Output Path: `[output_dir]`
   - Target Format: `[format]`
   - Playlist: `[playlist]`
   - Action: "This will run yt-dlp on local hardware. Proceed? (y/N)"
   - Require explicit approval before initiating download.
2. Validate the URL format and check if local network access is available.
3. Construct the shell command arguments based on parameters:
   - **Video Mode:** `yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"`
   - **Audio Mode:** `yt-dlp -x --audio-format mp3 --audio-quality 0`
   - **Playlist Handling:** Set `--no-playlist` if `playlist` is `false`.
   - **Metadata Integration:** Add `--embed-thumbnail --embed-metadata --write-subs` if `embed_metadata` is `true`.
   - **Output Mapping:** Set `-o "<output_dir>/%(title)s.%(ext)s"`.
4. Execute the command in the shell environment.
5. Stream progress logs back to the user/boss.
6. On success:
   - Extract title and output file path.
   - Record downloded item in `~/life/daily/<today>.md` or the corresponding project logs folder.
7. On failure: retry with `--force-ipv4` or update `yt-dlp` using `yt-dlp -U`.

## Side Effects
- Uses network bandwidth to download media assets.
- Writes media files (.mp4, .mp3, etc.) to the local filesystem.
- May write logs to daily Markdown notes.

## Related Skills
- dry_run_gate
- publish_podcast
