# 99-EXERCISES — Extra Labs and Scenarios

Cross-module exercises for consolidation.

## Lab guidato

### Lab 01 — Mini desktop companion full-cycle

Build, ship, and post-mortem a minimal companion app:
1. Single window app with isometric room background.
2. Animated chibi character idle/walk/wave.
3. Save/load with v1 schema; test migration to v2 (add new field).
4. Export Windows installer + Linux AppImage.
5. Profile to ensure 60 FPS active, 15 FPS idle.
6. Document: README + screenshots + performance metrics.

### Lab 02 — Isometric tile-based mini-game

Build a 2-room iso game:
1. TileMapLayer with custom TileSet, terrains.
2. Character pathfinds via Navigation.
3. Persistent state (door unlocked, etc.) saved.
4. Shader: outline on hover; fade-out transition.

### Lab 03 — CI/CD pipeline

GitHub Actions workflow that:
1. On push to `main`, runs `godot --check-only` for syntax errors.
2. On tag push (`v*`), exports Windows + Linux + Android.
3. Uploads to GitHub Release.
4. Notifies Slack on completion.

## Scenarios

- `scenario-01-bsod-crash-on-load.md` — Game crashes when loading old save; root cause and fix.
- `scenario-02-fps-cliff-on-zoom.md` — FPS drops from 60 to 15 when zoomed out; identify and optimize.
- `scenario-03-autoload-init-order-bug.md` — Autoload fails because depends on another not yet initialized.
- `scenario-04-export-fails-on-android.md` — Android export fails post-Godot-upgrade; troubleshoot.

## Scenario 01 — BSOD on load

**Symptoms**: Loading save from old version crashes with "expected dict, got null".

**Root cause**: Missing schema version migration; new field accessed without default.

**Fix**: Implement migration chain v1 → v2 with default values; never crash on missing keys.

## Scenario 02 — FPS cliff on zoom out

**Symptoms**: 60 FPS at default zoom; 15 FPS when zoomed out 2x.

**Root cause**: More draw calls visible; particle systems on screen multiply.

**Fix**: Disable offscreen particles; LOD via culling; or reduce particle count.

## Scenario 03 — Autoload init order

**Symptoms**: `SaveManager._ready` fails because `Config.api_url == ""`.

**Root cause**: `SaveManager` alphabetically before `Config`; runs first.

**Fix**: Rename autoload (`AAA_Config` is hack) or use defer pattern + `await Config.ready`.

## Scenario 04 — Android export fails

**Symptoms**: After Godot upgrade 4.4 → 4.5, Android export gives Java error.

**Root cause**: Export templates not updated; Android SDK version mismatch.

**Fix**: Re-download export templates; update Android SDK; verify build-tools version matches Godot requirement.
