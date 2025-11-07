# HuggingFace Model Access Guide

## Required Action

You need to accept user conditions for an additional pyannote model to enable speaker detection.

---

## Step-by-Step Instructions

### 1. Visit the Model Page
🔗 https://huggingface.co/pyannote/segmentation-3.0

### 2. Accept User Conditions
- Log in with your HuggingFace account (same one you used for speaker-diarization-3.1)
- Read the terms of use
- Click "Agree and access repository"

### 3. Wait for Access (Usually Instant)
- Most gated models grant access immediately
- Occasionally may take a few minutes
- You'll see a confirmation message when access is granted

### 4. Verify Access Granted
Run the setup test to confirm:
```bash
source venv/bin/activate
export HF_TOKEN=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
python test_setup.py
```

Look for this section in the output:
```
5. Speaker Diarization Test
--------------------------------------------------------------------------------
  Testing pyannote.audio...
  ✓ OK - Model loaded successfully
```

---

## Why This Model is Needed

**Model Dependency Chain:**
```
pyannote/speaker-diarization-3.1 (APPROVED)
  └── pyannote/segmentation-3.0 (PENDING)
```

The speaker diarization model you already approved depends on the segmentation model internally. The segmentation model:
- Breaks audio into segments
- Extracts speaker embeddings
- Enables the diarization model to cluster segments by speaker

Without segmentation-3.0, the diarization model cannot function.

---

## What Happens After Access is Granted

### Automatic First-Run Download
The first time you run speaker detection:
- Models will download (~500MB total)
- Cached in `~/.cache/huggingface/`
- Subsequent runs use cached models (fast)

### Processing Timeline
- **Initial model download**: 2-5 minutes (one-time)
- **Per-file processing**: 30-60 seconds each
- **Total for 3 files**: ~5 minutes after download

---

## Troubleshooting

### "Still getting 403 error after accepting"
- Wait 2-3 minutes and try again
- Clear cache: `rm -rf ~/.cache/huggingface/`
- Verify you're logged into the correct account
- Check https://huggingface.co/settings/tokens shows your token

### "Model download is very slow"
- Normal for first run (~500MB)
- Download happens only once
- Consider running overnight if bandwidth limited

### "Can I use a different model?"
Yes, but not recommended:
- `pyannote/segmentation-3.0` is the official dependency
- Alternative models may have compatibility issues
- Would require script modifications

---

## Alternative Options (If Blocked)

### Option 1: Use Current Results (Recommended if Urgent)
- Current 58 statements are already 95% excellent quality
- Only 3 files >5s duration
- Can proceed without enhancement

### Option 2: Manual Review
- Listen to the 3 flagged files:
  ```
  02.05.02, Listen and Choose, Module 2, Statement 001.mp3 (7.25s)
  02.05.02, Listen and Choose, Module 2, Statement 002.mp3 (6.78s)
  02.03.01, Listen and Choose, Module 1, Statement 002.mp3 (5.11s)
  ```
- Manually split at speaker changes if needed
- Use Audacity or similar audio editor

### Option 3: Wait for Access
- Usually granted within minutes
- Safe to check back in 10-15 minutes
- No action required on your part after accepting terms

---

## Security Notes

**Your HuggingFace Token:**
- Token: `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`
- Scope: Read-only access to approved models
- Stored in: Environment variable (not committed to git)
- Valid until: You revoke it at https://huggingface.co/settings/tokens

**Model License:**
- pyannote models are MIT licensed
- Academic and commercial use allowed
- Attribution required (included in our scripts)
- No additional restrictions

---

## Questions?

**"Do I need to do this for every project?"**
No - once you accept terms for a model, your HuggingFace account has permanent access.

**"Will this work offline after download?"**
Yes - models are cached locally. Initial run needs internet for download only.

**"Can I share the models with the team?"**
No - each team member needs their own HuggingFace account and token. Models can be cached on shared infrastructure after each person obtains access.

**"What if I lose access?"**
Unlikely - access is permanent once granted. If you see 403 errors later, your token may have expired or been revoked.

---

## Ready to Proceed?

Once you've accepted the terms and verified access:

```bash
# Run the complete workflow
cd /home/blackthorne/Work/tstprep.com/toefl-2026/audio-file-extraction
source venv/bin/activate
export HF_TOKEN=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

# Test on one file first
python split_with_speaker_detection.py \
  "input/02.05.02, Listen and Choose, Module 2.mp3" \
  output/test_speaker_detection

# If successful, reprocess all suspicious files
python reprocess_statements.py --suspicious-only
```

See `PROGRESS_REPORT.md` for detailed next steps.
