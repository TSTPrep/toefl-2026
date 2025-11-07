#!/usr/bin/env python3
"""
Audio Analysis Tool
Analyzes audio files for potential multi-statement issues using waveform and energy analysis
"""

import subprocess
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import sys

try:
    from pydub import AudioSegment
except ImportError:
    print("ERROR: pydub not installed. Install with: pip install pydub")
    sys.exit(1)


def load_audio(file_path):
    """Load audio file and convert to numpy array."""
    audio = AudioSegment.from_mp3(file_path)

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(1)

    # Get samples as numpy array
    samples = np.array(audio.get_array_of_samples())

    # Normalize to [-1, 1]
    samples = samples.astype(np.float32) / (2**15)

    return samples, audio.frame_rate


def calculate_energy(samples, window_size=512, hop_size=256):
    """Calculate energy (RMS) over time."""
    energy = []
    for i in range(0, len(samples) - window_size, hop_size):
        window = samples[i:i + window_size]
        rms = np.sqrt(np.mean(window**2))
        energy.append(rms)

    return np.array(energy)


def detect_potential_splits(energy, frame_rate, hop_size, threshold_percentile=30):
    """
    Detect potential split points based on energy drops.

    Returns list of (time, energy_drop) tuples
    """
    # Calculate energy drops (where energy decreases significantly)
    energy_diff = np.diff(energy)

    # Find local minima in energy
    threshold = np.percentile(energy, threshold_percentile)

    potential_splits = []
    for i in range(1, len(energy) - 1):
        # Check if this is a local minimum and below threshold
        if energy[i] < threshold:
            if energy[i] < energy[i-1] and energy[i] < energy[i+1]:
                time_sec = (i * hop_size) / frame_rate
                potential_splits.append((time_sec, energy[i]))

    return potential_splits


def visualize_audio(file_path, output_path=None):
    """Create visualization of audio waveform and energy."""
    print(f"Analyzing: {file_path}")

    # Load audio
    samples, frame_rate = load_audio(file_path)
    duration = len(samples) / frame_rate

    print(f"  Duration: {duration:.2f}s")
    print(f"  Sample rate: {frame_rate} Hz")
    print(f"  Samples: {len(samples)}")

    # Calculate energy
    hop_size = 256
    window_size = 512
    energy = calculate_energy(samples, window_size, hop_size)
    energy_times = np.arange(len(energy)) * hop_size / frame_rate

    # Detect potential splits
    potential_splits = detect_potential_splits(energy, frame_rate, hop_size)

    print(f"  Potential split points: {len(potential_splits)}")

    # Create visualization
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Plot 1: Waveform
    time_axis = np.arange(len(samples)) / frame_rate
    axes[0].plot(time_axis, samples, linewidth=0.5, alpha=0.7)
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title(f'Waveform: {Path(file_path).name}')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlim([0, duration])

    # Mark potential splits
    for split_time, _ in potential_splits:
        axes[0].axvline(x=split_time, color='red', linestyle='--', alpha=0.5)

    # Plot 2: Energy (RMS)
    axes[1].plot(energy_times, energy, linewidth=1, color='orange')
    axes[1].set_ylabel('Energy (RMS)')
    axes[1].set_title('Energy over Time')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlim([0, duration])

    # Mark threshold
    threshold = np.percentile(energy, 30)
    axes[1].axhline(y=threshold, color='green', linestyle='--', alpha=0.5, label=f'Threshold (30th percentile)')

    # Mark potential splits
    for split_time, split_energy in potential_splits:
        axes[1].axvline(x=split_time, color='red', linestyle='--', alpha=0.5)
        axes[1].plot([split_time], [split_energy], 'ro', markersize=8)

    axes[1].legend()

    # Plot 3: Energy derivative (to spot transitions)
    energy_diff = np.diff(energy)
    energy_diff_times = energy_times[:-1]
    axes[2].plot(energy_diff_times, energy_diff, linewidth=1, color='purple')
    axes[2].set_ylabel('Energy Change')
    axes[2].set_xlabel('Time (seconds)')
    axes[2].set_title('Energy Derivative (Rate of Change)')
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=0, color='black', linestyle='-', alpha=0.3)
    axes[2].set_xlim([0, duration])

    # Mark potential splits
    for split_time, _ in potential_splits:
        axes[2].axvline(x=split_time, color='red', linestyle='--', alpha=0.5)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"  Saved visualization to: {output_path}")
    else:
        plt.show()

    plt.close()

    return {
        'duration': duration,
        'potential_splits': potential_splits,
        'avg_energy': np.mean(energy),
        'energy_std': np.std(energy)
    }


def analyze_directory(directory, output_dir=None):
    """Analyze all MP3 files in directory."""
    directory = Path(directory)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    mp3_files = sorted(directory.glob('*.mp3'))

    if not mp3_files:
        print(f"No MP3 files found in {directory}")
        return

    print(f"\nAnalyzing {len(mp3_files)} files in {directory.name}...\n")

    results = []
    for mp3_file in mp3_files:
        output_path = None
        if output_dir:
            output_path = output_dir / f"{mp3_file.stem}_analysis.png"

        result = visualize_audio(str(mp3_file), str(output_path) if output_path else None)
        result['filename'] = mp3_file.name
        results.append(result)
        print()

    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"{'Filename':<50} {'Duration':>10} {'Splits':>8}")
    print("-"*80)

    for result in results:
        print(f"{result['filename']:<50} {result['duration']:>9.1f}s {len(result['potential_splits']):>8}")

    print("\nFiles with multiple potential split points (likely multi-statement):")
    multi_statement = [r for r in results if len(r['potential_splits']) >= 2]
    if multi_statement:
        for result in multi_statement:
            print(f"  - {result['filename']}: {len(result['potential_splits'])} potential splits")
    else:
        print("  None detected (or all files are single statements)")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze audio files for multi-statement detection'
    )
    parser.add_argument(
        'input',
        help='Input MP3 file or directory'
    )
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for visualizations',
        default=None
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"ERROR: Path not found: {input_path}")
        sys.exit(1)

    if input_path.is_file():
        # Single file
        output_path = None
        if args.output_dir:
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}_analysis.png"

        visualize_audio(str(input_path), str(output_path) if output_path else None)

    elif input_path.is_dir():
        # Directory
        analyze_directory(input_path, args.output_dir)

    else:
        print(f"ERROR: Invalid path: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()
