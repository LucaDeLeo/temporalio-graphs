# Spike Directory Structure

```
/Users/luca/dev/bounty/spike/
│
├── EXECUTIVE_SUMMARY.md          ← Start here for decision makers
├── QUICK_REFERENCE.md             ← TL;DR and quick commands
├── findings.md                    ← Detailed technical analysis (2,500+ words)
├── README.md                      ← Getting started guide
├── STRUCTURE.md                   ← This file
│
└── temporal-spike/                ← Python project (uv managed)
    ├── pyproject.toml            ← Dependencies (temporalio==1.7.1)
    ├── README.md                 ← Project-specific readme
    ├── output_diagrams.md        ← Visual comparison of outputs
    │
    ├── activities.py             ← Test activity definitions
    ├── workflow.py               ← Test workflow definition
    │
    ├── approach1_mock_activities.py       ← Approach 1 (full Temporal)
    ├── approach1_simplified.py            ← Approach 1 (simplified)
    ├── approach2_history_parsing.py       ← Approach 2
    ├── approach3_static_analysis.py       ← Approach 3 ⭐ RECOMMENDED
    │
    └── run_all_approaches.py              ← Compare all three
```

## Reading Order

1. **Quick Overview:** `QUICK_REFERENCE.md` (1 min)
2. **Decision Document:** `EXECUTIVE_SUMMARY.md` (5 min)
3. **Technical Details:** `findings.md` (15 min)
4. **Try It Out:** Run `temporal-spike/run_all_approaches.py`
5. **Dive Deeper:** Read individual approach files

## Key Files by Purpose

### For Decision Makers
- `EXECUTIVE_SUMMARY.md` - Decision, rationale, next steps
- `QUICK_REFERENCE.md` - One-page overview

### For Engineers
- `findings.md` - Complete technical analysis
- `approach3_static_analysis.py` - Recommended implementation
- `output_diagrams.md` - Visual examples

### For Quick Testing
- `run_all_approaches.py` - See all three approaches in action
- `README.md` - Getting started commands

## Running the Demos

```bash
# Navigate to project
cd /Users/luca/dev/bounty/spike/temporal-spike

# Run all approaches and compare
uv run python run_all_approaches.py

# Or run individually
uv run python approach1_simplified.py
uv run python approach2_history_parsing.py
uv run python approach3_static_analysis.py
```

## File Sizes

| File | Lines | Purpose |
|------|-------|---------|
| findings.md | ~420 | Comprehensive analysis |
| EXECUTIVE_SUMMARY.md | ~220 | Management summary |
| approach3_static_analysis.py | ~225 | Recommended prototype |
| approach2_history_parsing.py | ~155 | History-based prototype |
| approach1_simplified.py | ~145 | Mock-based prototype |

## Dependencies

- Python 3.13
- temporalio 1.7.1
- uv (package manager)

Install with: `cd temporal-spike && uv sync`

## Artifacts Generated

Each approach generates:
- Execution paths (list of activity sequences)
- Mermaid diagram (text format)
- Performance metrics
- Evaluation analysis

## Success Metrics

All files demonstrate:
- ✅ 2 paths generated (2^1 for 1 decision)
- ✅ Valid Mermaid output
- ✅ < 5 second execution
- ✅ Clear recommendation

## Next Steps

1. Review `EXECUTIVE_SUMMARY.md` for decision
2. Read `findings.md` for technical details
3. Examine `approach3_static_analysis.py` for implementation
4. Proceed with full development (see findings.md Phase 1-3)
