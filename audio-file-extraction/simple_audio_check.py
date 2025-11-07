#!/usr/bin/env python3
"""
Simple Audio Analysis using ffmpeg only
Checks audio characteristics to identify potential multi-statement files
"""

import subprocess
import json
from pathlib import Path
import argparse


def get_audio_info(file_path):
    """Get detailed audio information using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(file_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"ERROR getting info for {file_path}: {e}")
        return None


def detect_silences_detailed(file_path, threshold_db=-50, min_duration=0.2):
    """Detect silences with detailed information."""
    cmd = [
        'ffmpeg', '-i', str(file_path),
        '-af', f'silencedetect=noise={threshold_db}dB:d={min_duration}',
        '-f', 'null', '-'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        silences = []
        lines = result.stderr.split('\n')

        silence_start = None
        for line in lines:
            if 'silence_start' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'silence_start:':
                        silence_start = float(parts[i+1])

            elif 'silence_end' in line and silence_start is not None:
                parts = line.split()
                silence_end = None
                silence_duration = None

                for i, part in enumerate(parts):
                    if part == 'silence_end:':
                        silence_end = float(parts[i+1])
                    elif part == 'silence_duration:':
                        silence_duration = float(parts[i+1])

                if silence_end:
                    silences.append({
                        'start': silence_start,
                        'end': silence_end,
                        'duration': silence_duration or (silence_end - silence_start)
                    })
                silence_start = None

        return silences

    except Exception as e:
        print(f"ERROR detecting silences in {file_path}: {e}")
        return []


def analyze_file(file_path, silence_threshold=-50):
    """Analyze a single audio file."""
    print(f"\nAnalyzing: {Path(file_path).name}")
    print("-" * 80)

    # Get basic info
    info = get_audio_info(file_path)
    if not info:
        return None

    duration = float(info['format']['duration'])
    bitrate = int(info['format'].get('bit_rate', 0)) / 1000  # Convert to kbps

    print(f"  Duration: {duration:.2f}s")
    print(f"  Bitrate: {bitrate:.0f} kbps")
    print(f"  Size: {int(info['format']['size']) / 1024:.1f} KB")

    # Detect silences
    silences = detect_silences_detailed(file_path, threshold_db=silence_threshold)

    if silences:
        print(f"\n  Detected {len(silences)} silence periods:")
        for i, silence in enumerate(silences, 1):
            print(f"    {i}. {silence['start']:.2f}s - {silence['end']:.2f}s (duration: {silence['duration']:.2f}s)")

        # Calculate speech segments (between silences)
        speech_segments = []
        prev_end = 0

        for silence in silences:
            if silence['start'] > prev_end:
                speech_segments.append({
                    'start': prev_end,
                    'end': silence['start'],
                    'duration': silence['start'] - prev_end
                })
            prev_end = silence['end']

        # Add final segment if any
        if prev_end < duration:
            speech_segments.append({
                'start': prev_end,
                'end': duration,
                'duration': duration - prev_end
            })

        if speech_segments:
            print(f"\n  Speech segments: {len(speech_segments)}")
            for i, seg in enumerate(speech_segments, 1):
                print(f"    {i}. {seg['start']:.2f}s - {seg['end']:.2f}s (duration: {seg['duration']:.2f}s)")

            # Check for potential multi-statement indicators
            avg_segment_duration = sum(s['duration'] for s in speech_segments) / len(speech_segments)
            print(f"\n  Average speech segment duration: {avg_segment_duration:.2f}s")

            if len(speech_segments) > 1:
                print(f"  ⚠️  Multiple speech segments detected - possible multi-statement file")
            else:
                print(f"  ✓ Single continuous speech segment")

    else:
        print("  No silences detected")

    return {
        'filename': Path(file_path).name,
        'duration': duration,
        'silence_count': len(silences),
        'silences': silences
    }


def analyze_directory(directory, threshold=-50):
    """Analyze all MP3 files in a directory."""
    directory = Path(directory)
    mp3_files = sorted(directory.glob('*.mp3'))

    if not mp3_files:
        print(f"No MP3 files found in {directory}")
        return

    print(f"\n{'='*80}")
    print(f"ANALYZING DIRECTORY: {directory.name}")
    print(f"Found {len(mp3_files)} MP3 files")
    print(f"{'='*80}")

    results = []
    for mp3_file in mp3_files:
        result = analyze_file(str(mp3_file), threshold)
        if result:
            results.append(result)

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Filename':<50} {'Duration':>10} {'Silences':>10}")
    print("-" * 80)

    for result in results:
        print(f"{result['filename']:<50} {result['duration']:>9.1f}s {result['silence_count']:>10}")

    # Flag suspicious files
    print("\n\nPotential multi-statement files (multiple silences):")
    multi_silence = [r for r in results if r['silence_count'] >= 2]

    if multi_silence:
        for result in multi_silence:
            print(f"  - {result['filename']}: {result['silence_count']} silence periods")
    else:
        print("  None detected")


def main():
    parser = argparse.ArgumentParser(
        description='Simple audio analysis using ffmpeg'
    )
    parser.add_argument(
        'input',
        help='Input MP3 file or directory'
    )
    parser.add_argument(
        '-t', '--threshold',
        type=int,
        default=-50,
        help='Silence detection threshold in dB (default: -50)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Path not found: {input_path}")
        return

    if input_path.is_file():
        analyze_file(str(input_path), args.threshold)
    elif input_path.is_dir():
        analyze_directory(input_path, args.threshold)
    else:
        print(f"ERROR: Invalid path: {input_path}")


if __name__ == '__main__':
    main()
