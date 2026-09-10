# VoiceGuide

## 🧪 Voice Interruption & Recovery Evidence

We have built a dedicated test harness to prove our system achieves sub-500ms interruption latency using LiveKit and Rime TTS.

**To run the test harness:**
1. Install dependencies: `pip install -r requirements.txt`
2. Run the mock session: `python testing-evidence-Nihal/scripts/test_interruption.py --runs 5`

**To generate the final evidence document:**
1. Generate markdown: `python testing-evidence-Nihal/scripts/generate_evidence.py`

You can view our latest automated test results in [testing-evidence-Nihal/RIME_EVIDENCE.md](testing-evidence-Nihal/RIME_EVIDENCE.md).
