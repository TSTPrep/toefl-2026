# TOEFL Audio Splitting - Quick Reference Card

## Files

- **CSV**: `Sequence.csv` (256 segments)
- **Audio**: `Listening - Audio File - Master.mp3` (37 min, 71 MB)
- **Output**: `output/segments/` (256 MP3 files, ~80 MB)

## Timecode Conversion

**Format**: `HH:MM:SS:FF` (25 fps)

```python
seconds = (H * 3600) + (M * 60) + S + (F / 25)
```

| Timecode | Seconds |
|----------|---------|
| 00:00:00:00 | 0.000 |
| 00:00:02:15 | 2.600 |
| 00:01:06:04 | 66.160 |

## ffmpeg Command

```bash
ffmpeg -i "Listening - Audio File - Master.mp3" \
       -ss START_SEC -t DURATION_SEC \
       -acodec libmp3lame -b:a 256k -ar 44100 -ac 2 \
       -y "output.mp3"
```

## File Naming

```
segment_0001_speaker1_00-00-00-00_to_00-00-02-15.mp3
```

## Validation Checklist

- [ ] Pre: CSV valid, timestamps sequential, disk space OK
- [ ] During: ffmpeg success, file exists, duration matches
- [ ] Post: 256 files, all playable, total duration matches

## Performance

- **Time**: 10-15 minutes
- **Output**: 256 segments (~80 MB)
- **Speed**: ~2-4 seconds per segment

## Next Steps

1. Read `AUDIO_SPLITTING_PLAN.md` (detailed spec)
2. Implement `scripts/split_audio.py`
3. Test with 5 segments
4. Run full extraction (256 segments)
5. Validate output

## Documentation

- **Detailed Plan**: `AUDIO_SPLITTING_PLAN.md` (50 pages)
- **Summary**: `OPTION3_ANALYSIS_SUMMARY.md` (5 pages)
- **This Card**: Quick reference (1 page)
