# Bank Scaffold Before / After Sample

## Before

Before issue #2, `generate_playlist.py` required `--catalog`. When a lane only
had Tony Mode B documentation and no categorized JSON, the operator had two bad
choices:

```bash
python skills/playlist-builder/scripts/generate_playlist.py \
  --context skills/playlist-builder/contexts/yoga-power.json \
  --theme "pratyahara inward focus"
```

Result:

```text
error: the following arguments are required: --catalog
```

If an agent wrote a playlist anyway, it had to improvise search rows outside the
tooling, which made the distinction between tracklist, search-assisted output,
and documentation-only bank references too easy to blur.

## After

The generator can now produce a first-class bank scaffold:

```bash
python skills/playlist-builder/scripts/generate_playlist.py \
  --context skills/playlist-builder/contexts/yoga-power.json \
  --skill-dir skills/playlist-builder \
  --catalog-state bank-scaffold \
  --include-example-candidates \
  --theme "pratyahara inward focus"
```

Result shape:

```text
Output mode: bank-scaffold
Slot plan with banks A/B/C/D/E, target track counts, search strings,
exact_id_status=requires_auth, verification_required=true,
platform_auth_available=false, and Tony bank-reference URLs.
```

See `examples/bank_scaffold_pratyahara_after.md` for a full sample.
