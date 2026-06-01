# Building & Exporting Games — From Source to Player

> **Course module:** Godot 4 in Production
> **Position:** Phase 4 — Production · Module 11
> **Prerequisites:** Modules 01-10.
> **Learning objectives:** Godot export templates; Windows installer (Inno Setup); Linux AppImage; macOS notarization; Android APK/AAB; CI/CD with GitHub Actions; pre-release checklist.
> **Estimated time:** 90 min reading · 360-480 min hands-on
> **Level:** proficient (Dreyfus 4)
> **Last updated:** 2026-04-27

## Guiding ideas

1. **Export templates per platform; pin version.** Godot 4.5 export templates ≠ 4.4 ≠ 4.6.
2. **Inno Setup is the Windows standard for Godot.** Free, scriptable, mature.
3. **macOS = notarization.** Apple won't run unsigned apps without warning users; cost = $99/year Apple Developer.
4. **Android AAB > APK.** AAB = smaller download, mandatory for Google Play 2021+.
5. **CI/CD pipeline = reproducibility.** Manual builds = hidden config = "works on my machine".

A comprehensive study of how games go from source code to playable executables: compilation, Godot's export system, platform-specific builds, CI/CD pipelines, distribution platforms, optimization, and how real companies ship games.

---

## 1. How Game "Compilation" Works

### Compiled vs Interpreted vs Bytecode

Games can be built in different ways depending on the engine and language:

```
COMPILED (C, C++, Rust):
  Source Code → Compiler → Machine Code (.exe)
  ✓ Maximum performance
  ✗ Must compile for each platform separately
  Examples: Unreal Engine (C++), custom engines

INTERPRETED (Python, Lua):
  Source Code → Interpreter reads line by line → Executes
  ✓ Cross-platform (interpreter handles differences)
  ✗ Slower than compiled
  Examples: Some modding tools, prototyping

BYTECODE (GDScript, C#, Java):
  Source Code → Compiler → Bytecode → Virtual Machine → Executes
  ✓ Faster than interpreted, cross-platform
  ✓ GDScript compiles to bytecode at export time
  Examples: Godot (GDScript), Unity (C# → IL)
```

### What Happens When Godot "Exports"

```
Your Godot Project:
├── scripts/*.gd           (GDScript source)
├── scenes/*.tscn           (Scene definitions)
├── assets/sprites/*.png    (Textures)
├── assets/audio/*.wav      (Audio files)
├── data/*.json             (Game data)
└── project.godot           (Configuration)

    ↓ Export Process ↓

Step 1: GDScript Compilation
  .gd files → GDScript bytecode (.gdc)
  (Faster execution, source code not exposed)

Step 2: Resource Conversion
  .png → Compressed textures (S3TC, ETC2, or ASTC depending on platform)
  .wav → May stay as WAV or convert to OGG
  .tscn → Binary scene format
  .tres → Binary resource format

Step 3: Packing
  All converted resources → single .pck file (PCK = "pack")

Step 4: Bundling
  Export Template (platform binary) + .pck → Final executable

Final output:
  Windows: MiniCozyRoom.exe + MiniCozyRoom.pck (or embedded)
  macOS:   MiniCozyRoom.app (contains both)
  Linux:   MiniCozyRoom.x86_64 + MiniCozyRoom.pck
  Web:     MiniCozyRoom.html + MiniCozyRoom.wasm + MiniCozyRoom.pck
```

---

## 2. Godot Export System in Detail

### Export Templates

Export templates are **pre-compiled Godot engine binaries** for each platform. They contain the engine code but NOT your game — your game is the .pck file.

```
Export Template = Godot Engine compiled for a specific platform
                  (without the editor, just the runtime)

Types:
  Debug template:   Includes debugging tools, larger file, slower
                    Use for: testing, development builds

  Release template: Optimized, smaller, faster, no debug tools
                    Use for: final distribution

Download:
  Editor → Export → Manage Export Templates → Download
  or: https://godotengine.org/download
```

### Export Presets

Export presets configure how your game is exported for each platform:

```
In Godot Editor: Project → Export → Add...

Preset configuration:
┌─────────────────────────────────────────────┐
│ Export Preset: "Windows Desktop"              │
│                                               │
│ Platform:    Windows Desktop                  │
│ Template:    Release                          │
│ Binary:      godot.windows.template_release   │
│                                               │
│ Application:                                  │
│   Name:           Relax Room              │
│   Icon:           res://icon.ico              │
│   Version:        1.0.0                       │
│                                               │
│ Resources:                                    │
│   Include:        *.gd, *.tscn, *.tres,       │
│                   *.json, *.png, *.wav         │
│   Exclude:        *.md, *.txt, tests/*        │
│                                               │
│ Features:                                     │
│   Custom:         [gl_compatibility]           │
└─────────────────────────────────────────────┘
```

### PCK Files

The `.pck` file is a **packed resource file** containing all your game's assets:

```
MiniCozyRoom.pck contents:
├── .godot/
│   └── imported/           (processed resources)
├── scripts/
│   ├── autoload/
│   │   ├── signal_bus.gdc  (compiled GDScript)
│   │   ├── logger.gdc
│   │   └── ...
│   └── ...
├── scenes/
│   └── ... (.tscn converted to binary)
├── data/
│   ├── rooms.json
│   ├── decorations.json
│   └── ...
├── assets/
│   └── ... (compressed textures)
└── project.binary           (compiled project.godot)
```

**Key points about PCK:**
- Can be embedded inside the .exe (single-file distribution)
- Can be encrypted (protects assets and scripts)
- Can be updated independently of the executable (patching!)
- Uses its own virtual filesystem (res:// maps to PCK contents)

### Encrypted Exports

To protect your game's assets and scripts:

```
In Export settings:
  Encryption:
    Encrypt PCK: ✓
    Encryption Key: [256-bit hex key]

This prevents:
  - Casual extraction of sprites/music
  - Reading GDScript source (it's bytecode + encrypted)

This does NOT prevent:
  - Determined reverse engineering (nothing does)
  - Memory dumping at runtime
  - Screenshot/recording of assets
```

### Feature Tags

Feature tags let you run different code paths on different platforms:

```gdscript
# Built-in feature tags:
if OS.has_feature("windows"):
    # Windows-specific code
elif OS.has_feature("web"):
    # Web-specific code (e.g., disable file import)
elif OS.has_feature("mobile"):
    # Mobile-specific code

# Custom feature tags (set in Export Preset):
if OS.has_feature("demo"):
    # Demo version — limit features
if OS.has_feature("steam"):
    # Steam version — enable achievements

# Our project uses this in music_panel.gd:
func _on_import_pressed() -> void:
    if OS.has_feature("web"):
        AppLogger.warn("MusicPanel", "File import not supported on web")
        return
    # ... open file dialog
```

---

## 3. Platform-Specific Building

### Windows

```
Output:  MiniCozyRoom.exe (+ MiniCozyRoom.pck or embedded)
Size:    ~50-80 MB (engine + assets)

Options:
  - Console output: Disable for release (no black terminal window)
  - Icon: .ico file (multiple sizes: 16, 32, 48, 256)
  - Embed PCK: ✓ (single .exe file distribution)

Code Signing:
  Why:  Without signing, Windows shows "Unknown publisher" warning
  How:  Purchase a code signing certificate ($200-400/year)
        signtool sign /f cert.pfx /p password MiniCozyRoom.exe
  Note: Optional for indie games distributed via itch.io/Steam

Installer Creation:
  NSIS (Nullsoft Scriptable Install System):
    - Free and open source
    - Creates .exe installer with wizard
    - Handles Start Menu shortcuts, uninstaller

  Inno Setup:
    - Free, widely used
    - Easy script-based configuration
    - Professional-looking installer

  Example Inno Setup script:
    [Setup]
    AppName=Relax Room
    AppVersion=1.0.0
    DefaultDirName={autopf}\MiniCozyRoom
    OutputBaseFilename=MiniCozyRoom-Setup
    Compression=lzma2
    SolidCompression=yes

    [Files]
    Source: "build\MiniCozyRoom.exe"; DestDir: "{app}"
    Source: "build\MiniCozyRoom.pck"; DestDir: "{app}"

    [Icons]
    Name: "{group}\Relax Room"; Filename: "{app}\MiniCozyRoom.exe"
    Name: "{commondesktop}\Relax Room"; Filename: "{app}\MiniCozyRoom.exe"
```

### macOS

```
Output:  MiniCozyRoom.app (application bundle)

Bundle structure:
  MiniCozyRoom.app/
  └── Contents/
      ├── Info.plist        (metadata: name, version, icon)
      ├── MacOS/
      │   └── MiniCozyRoom  (executable binary)
      ├── Resources/
      │   ├── MiniCozyRoom.pck
      │   └── icon.icns     (macOS icon format)
      └── Frameworks/        (shared libraries if any)

Code Signing & Notarization:
  Required for: macOS Catalina and later (mandatory since 2020)
  Without it:   "MiniCozyRoom.app is damaged and can't be opened"

  Steps:
  1. Get Apple Developer account ($99/year)
  2. Create signing certificate in Xcode
  3. Sign: codesign --deep -s "Developer ID" MiniCozyRoom.app
  4. Notarize: xcrun notarytool submit MiniCozyRoom.zip --apple-id ...
  5. Staple: xcrun stapler staple MiniCozyRoom.app

DMG Creation:
  hdiutil create -volname "Relax Room" -srcfolder MiniCozyRoom.app \
    -ov -format UDZO MiniCozyRoom.dmg
```

### Linux

```
Output:  MiniCozyRoom.x86_64 (+ .pck or embedded)

Distribution formats:

  AppImage (recommended for indie games):
    - Single file, runs on any Linux distro
    - No installation needed
    - Download → chmod +x → run
    - Tool: appimagetool

  Flatpak:
    - Sandboxed distribution
    - Available on Flathub (like an app store)
    - More complex setup but wider reach

  .deb / .rpm:
    - Distro-specific packages
    - Only worthwhile if targeting specific distro
    - More work, less portable
```

### Web (HTML5)

```
Output:  MiniCozyRoom.html + .js + .wasm + .pck

Requirements:
  - HTTPS hosting (browsers require secure context for SharedArrayBuffer)
  - Server must set these headers:
    Cross-Origin-Opener-Policy: same-origin
    Cross-Origin-Embedder-Policy: require-corp

Limitations:
  - No filesystem access (no file import dialog)
  - No native file I/O (use IndexedDB via JavaScript bridge)
  - Audio requires user interaction to start (browser policy)
  - Larger download size (~20-40 MB)
  - Performance: 60-80% of native
  - Only GL Compatibility renderer works (our renderer! ✓)

Our project consideration:
  Relax Room COULD run as a web app because:
  ✓ Uses GL Compatibility renderer
  ✓ 2D only (no heavy GPU features)
  ✗ File import feature won't work (already handled with OS.has_feature("web"))
  ✗ SQLite plugin needs special web build
```

### Android

```
Output:  MiniCozyRoom.apk (direct install) or .aab (Google Play)

Requirements:
  - Android SDK + NDK
  - Java JDK 17+
  - Keystore for signing

Export settings:
  - Min SDK: 21 (Android 5.0) for maximum compatibility
  - Target SDK: 34 (Android 14) for Google Play requirement
  - Permissions: only what you need (INTERNET for Supabase)

Google Play requirements:
  - .aab format (not .apk) since August 2021
  - Target SDK must be within 1 year of latest Android
  - Privacy policy required
  - App content rating
  - $25 one-time developer fee
```

### iOS

```
Output:  MiniCozyRoom.ipa

Requirements:
  - macOS with Xcode (can't build iOS on Windows/Linux)
  - Apple Developer account ($99/year)
  - Provisioning profile
  - Physical iOS device for testing (or simulator)

App Store submission:
  - App review process (1-7 days)
  - Must follow Apple Human Interface Guidelines
  - No other app stores allowed on iOS
  - Apple takes 30% of revenue (15% for small businesses)
```

---

## 4. How Real Companies Build Games

### CI/CD Pipelines for Games

```
Developer commits code
         │
         ▼
CI Pipeline triggers (GitHub Actions / GitLab CI / Jenkins)
         │
         ├── 1. Code Quality
         │   ├── Lint GDScript (gdlint)
         │   ├── Format check (gdformat)
         │   └── Static analysis
         │
         ├── 2. Build
         │   ├── Export for Windows
         │   ├── Export for macOS
         │   ├── Export for Linux
         │   └── Export for Web
         │
         ├── 3. Test
         │   ├── Unit tests (GdUnit4)
         │   ├── Integration tests
         │   └── Smoke test (does it launch?)
         │
         ├── 4. Security
         │   ├── Secret scanning
         │   ├── Dependency audit
         │   └── License compliance
         │
         └── 5. Artifacts
             ├── Upload builds as artifacts
             ├── Generate changelog
             └── Notify team (Slack/Discord)
```

### Our CI Pipeline

```yaml
# .github/workflows/ci.yml (simplified)
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install gdtoolkit==4.*
      - run: gdlint v1/scripts/
      - run: gdformat --check v1/scripts/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: chickensoft-games/setup-godot@v2
        with: { version: '4.5', include-templates: false }
      - run: |
          godot --headless --path v1 \
            -s addons/gdUnit4/bin/GdUnitCmdTool.gd \
            --add "res://tests/"
```

### Build Servers and Build Farms

Large studios use dedicated build machines:

```
Build Farm:
┌────────────┐  ┌────────────┐  ┌────────────┐
│ Windows    │  │ macOS      │  │ Linux      │
│ Build      │  │ Build      │  │ Build      │
│ Server     │  │ Server     │  │ Server     │
│            │  │ (Mac Mini) │  │            │
│ Exports:   │  │ Exports:   │  │ Exports:   │
│ .exe       │  │ .app       │  │ .x86_64    │
│ .pck       │  │ .dmg       │  │ .AppImage  │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │                │               │
      └────────────────┼───────────────┘
                       │
                ┌──────▼──────┐
                │  Artifact   │
                │  Storage    │
                │  (S3/GCS)   │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │  QA Team    │
                │  Downloads  │
                │  and Tests  │
                └─────────────┘
```

### Nightly Builds

```
Every night at 2 AM:
  1. Fetch latest code from main branch
  2. Build for all platforms
  3. Run full test suite (including slow tests)
  4. Generate build report
  5. Email results to team

Morning:
  Team reads build report
  Green ✓ = everything works
  Red ✗ = someone broke the build yesterday → fix immediately
```

---

## 5. Distribution Platforms

### Steam

The most popular PC distribution platform:

```
Steamworks Setup:
  1. Register: partner.steamgames.com ($100 per game)
  2. Create App: assign App ID
  3. Configure: store page, screenshots, descriptions
  4. Upload: using SteamCMD or Steam Build tools

Build Upload:
  # Using SteamCMD
  steamcmd +login "username" +run_app_build "build_config.vdf" +quit

  # build_config.vdf defines:
  "AppBuild"
  {
    "AppID" "123456"
    "Desc" "Version 1.0.0"
    "ContentRoot" "./build/"
    "BuildOutput" "./output/"
    "Depots"
    {
      "123457"
      {
        "FileMapping"
        {
          "LocalPath" "windows/*"
          "DepotPath" "."
        }
      }
    }
  }

Steam Features for Developers:
  - Achievements: Track player milestones
  - Cloud Save: Sync saves across devices
  - Workshop: User-generated content (room themes, decorations)
  - Input: Gamepad remapping
  - Beta branches: Test with subset of users
  - Analytics: Play time, retention, concurrent players
```

### itch.io

The indie-friendly distribution platform:

```
Distribution via Butler CLI:
  # Install Butler
  curl -L https://broth.itch.ovh/butler/linux-amd64/LATEST/archive/default \
    | sudo tar xvz -C /usr/local/bin

  # Push a build
  butler push build/windows username/relax-room:windows
  butler push build/linux username/relax-room:linux
  butler push build/mac username/relax-room:mac

  # Butler features:
  - Delta patches (only uploads changed files)
  - Versioning (automatic version tracking)
  - Channels (windows, linux, mac, web)
  - Instant rollback

itch.io Benefits:
  - No registration fee
  - Developer sets revenue split (0-100%)
  - Direct relationship with players
  - No review process (publish instantly)
  - Good for prototypes, demos, game jams
```

### GOG (Good Old Games)

```
- DRM-free (no online requirement)
- Curation: GOG reviews and approves games
- Galaxy SDK: Optional achievements, cloud saves
- Revenue split: 70/30 (same as Steam)
- Smaller audience but more dedicated
```

---

## 6. Optimization for Release

### Debug vs Release Builds

```
Debug Build:                    Release Build:
├── Includes debugger symbols   ├── Stripped of debug info
├── Assertions active           ├── Assertions disabled
├── Verbose logging             ├── Minimal logging
├── Unoptimized code            ├── Compiler optimizations (-O2)
├── Larger file size (~80 MB)   ├── Smaller file size (~50 MB)
├── Slower execution            ├── Faster execution
└── Use for: development        └── Use for: distribution

In Godot:
  Debug: F5 in editor, or Export with Debug template
  Release: Export with Release template + strip debug symbols
```

### Texture Compression

Different platforms support different texture compression:

```
Platform       → Compression    → Quality → Size Reduction
Windows/macOS  → S3TC (BC/DXT)  → Good    → 6:1
Android        → ETC2           → Good    → 6:1
iOS            → ASTC           → Best    → 4:1 to 36:1
Web            → S3TC or ETC2   → Varies  → 6:1

For pixel art:
  IMPORTANT: Lossy compression can ruin pixel art!

  Best approach for pixel art:
  1. Keep textures as PNG (lossless)
  2. Use NEAREST filtering (no interpolation)
  3. Don't compress small textures (< 256x256)
  4. For spritesheets: use ETC2/ASTC with highest quality

In Godot Export Settings:
  Textures → Compress Format → VRAM Compressed (for 3D/large textures)
  or → Lossless (for pixel art)
```

### Audio Compression

```
Format   → Quality  → File Size → Use For
WAV      → Perfect  → Large     → Short SFX (< 5 seconds)
OGG      → Great    → Small     → Music, long audio, ambience
MP3      → Good     → Small     → Music (Godot 4 supports import)

Recommendation for our project:
  SFX (click, notification): WAV (small files, instant playback)
  Music tracks: OGG Vorbis at 128-192 kbps (good quality, small size)
  Ambience loops: OGG Vorbis at 96-128 kbps (background, less critical)

Conversion:
  ffmpeg -i track.wav -c:a libvorbis -q:a 5 track.ogg   # Quality 5 (~160 kbps)
  ffmpeg -i ambience.wav -c:a libvorbis -q:a 3 ambience.ogg  # Quality 3 (~112 kbps)
```

### File Size Reduction

```
Technique                  Savings    Effort
Remove unused assets       10-50%     Low (just delete unused files)
Compress textures          40-60%     Low (export setting)
Compress audio to OGG      60-80%     Low (convert WAV → OGG)
Use texture atlases        5-15%      Medium (combine sprites)
Strip debug symbols        10-20%     None (export setting)
Remove test files          1-5%       Low (exclude in export)
Use .pck compression       5-15%      None (export setting)

Our project estimate:
  Development build: ~150 MB
  Optimized release: ~40-60 MB
```

---

## 7. Versioning and Updates

### Semantic Versioning for Games

```
Version: MAJOR.MINOR.PATCH[-LABEL]

Examples:
  0.1.0-alpha    First playable prototype
  0.5.0-beta     Feature-complete, needs testing
  1.0.0          First public release
  1.1.0          Added new room themes
  1.1.1          Fixed crash bug
  1.2.0          Added inventory system
  2.0.0          Major redesign (save migration needed)

Pre-release labels:
  alpha:  Feature incomplete, bugs expected
  beta:   Feature complete, bugs being fixed
  rc.1:   Release candidate 1 (almost ready)
  rc.2:   Release candidate 2 (fixed rc.1 bugs)
```

### Patch Delivery

```
Full Update:
  Player downloads entire new build (50 MB)
  Simple but wasteful

Delta Update (patch):
  Player downloads only what changed (2 MB)
  Complex but efficient

  Steam handles this automatically (depot diff)
  itch.io Butler handles this automatically
  Custom: use bsdiff/bspatch or xdelta3

Save Compatibility:
  Version 1.0 save → Version 1.1 game
  MUST work! Use migration functions.

  Version 1.0 save → Version 2.0 game
  SHOULD work (with migration chain).
  If impossible, display clear message to player.
```

---

## 8. Legal and Business Requirements

### Software Licenses

```
Your game uses third-party code and assets. Know the licenses!

License          Can Sell?  Must Credit?  Must Open Source?
MIT              ✓ Yes      ✓ Yes        ✗ No
CC0              ✓ Yes      ✗ No         ✗ No
CC-BY            ✓ Yes      ✓ Yes        ✗ No
CC-BY-SA         ✓ Yes      ✓ Yes        ✓ Derivatives
Apache 2.0       ✓ Yes      ✓ Yes        ✗ No
GPL              ✓ Yes      ✓ Yes        ✓ All source code!
Proprietary      Varies     Varies       N/A

Our project:
  Godot Engine: MIT (free, credit in About screen)
  godot-sqlite: MIT (free, credit in About screen)
  Kenney assets: CC0 (free, no credit needed)
  Mixkit music: Free license (free, no credit needed)
  Other assets: Check each one!

IMPORTANT: GPL assets/code would require us to open-source
our entire game. We specifically avoid GPL for this reason.
```

### Credits and Attribution

```
Create a CREDITS or LICENSES screen in your game:

  Relax Room

  Engine: Godot Engine (MIT License)
          https://godotengine.org

  Plugins:
    godot-sqlite by 2shady4u (MIT License)

  Art Assets:
    Pixel UI Pack by Kenney (CC0)
    Indoor Plants by Spring Chicken (CC0)
    Tiny Town by Kenney (CC0)
    Free Pixel Art Forest by Eder Muniz

  Music:
    Tracks from Mixkit (Free License)

  Fonts:
    [List fonts used]
```

### Privacy (GDPR)

```
If your game collects ANY user data (including Supabase cloud sync):

Required:
  1. Privacy Policy — What data you collect, why, and how
  2. Consent — User must agree before data collection
  3. Right to Delete — User can request data deletion
  4. Data Minimization — Only collect what you need

Our project:
  - Supabase stores user account + save data → needs privacy policy
  - Offline mode collects nothing → no privacy concern
  - If publishing in EU: GDPR compliance mandatory
```

### Age Ratings

```
Platform    Rating System    Required?
PC (Steam)  IARC             Free, self-assessment questionnaire
Console     PEGI/ESRB        Paid, formal review ($$$)
Mobile      IARC             Free via Google Play/App Store

Our game: Likely rated PEGI 3 / ESRB E (Everyone)
  - No violence
  - No gambling
  - No online chat
  - No mature themes
```

---

## 9. Real-World Build Pipeline Example

### From Commit to Player Download

Here's a complete example of a professional indie build pipeline:

```
┌─────────────────────────────────────────────────────────┐
│  STEP 1: Developer pushes code to GitHub                 │
│                                                          │
│  $ git add scripts/autoload/audio_manager.gd             │
│  $ git commit -m "feat: add crossfade to audio player"   │
│  $ git push origin feature/audio-crossfade               │
└────────────────────┬────────────────────────────────────┘
                     │ GitHub webhook triggers CI
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 2: CI runs quality checks                          │
│                                                          │
│  ├── gdlint v1/scripts/ .............. ✓ No issues      │
│  ├── gdformat --check v1/scripts/ .... ✓ Formatted      │
│  ├── security scan ................... ✓ No secrets      │
│  └── unit tests ...................... ✓ 24/24 passed    │
└────────────────────┬────────────────────────────────────┘
                     │ All checks pass
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 3: Pull Request reviewed and merged                │
│                                                          │
│  Reviewer checks:                                        │
│  ├── Code quality ................... ✓ Approved         │
│  ├── Test coverage .................. ✓ Tests added      │
│  └── Documentation .................. ✓ Updated          │
│                                                          │
│  → Merged to main branch                                 │
└────────────────────┬────────────────────────────────────┘
                     │ Merge to main triggers build
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 4: Build pipeline exports for all platforms        │
│                                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │  GitHub Actions Runner (Ubuntu)               │        │
│  │                                                │        │
│  │  1. Install Godot 4.5 headless                 │        │
│  │  2. Import project (generate .import files)    │        │
│  │  3. Export:                                     │        │
│  │     ├── Windows: godot --export-release         │        │
│  │     │            "Windows Desktop"              │        │
│  │     │            build/windows/MiniCozyRoom.exe │        │
│  │     │                                           │        │
│  │     ├── Linux: godot --export-release            │        │
│  │     │          "Linux/X11"                       │        │
│  │     │          build/linux/MiniCozyRoom.x86_64   │        │
│  │     │                                            │        │
│  │     └── Web: godot --export-release               │        │
│  │              "Web"                                │        │
│  │              build/web/MiniCozyRoom.html          │        │
│  │                                                    │        │
│  │  4. Upload artifacts to GitHub Releases            │        │
│  └────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │ Builds available
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 5: Distribution                                    │
│                                                          │
│  ├── itch.io: butler push build/windows user/game:win    │
│  ├── Steam: steamcmd +run_app_build config.vdf           │
│  └── Website: upload web build to hosting                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  STEP 6: Player downloads and plays!                     │
│                                                          │
│  Player → itch.io/Steam/website → Downloads → Plays 🎮   │
└─────────────────────────────────────────────────────────┘
```

### Automated GitHub Actions Export

```yaml
# .github/workflows/export.yml
name: Export Game
on:
  push:
    tags: ['v*']  # Only on version tags (v1.0.0, v1.1.0, etc.)

jobs:
  export:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        platform: [windows, linux, web]
        include:
          - platform: windows
            preset: "Windows Desktop"
            extension: exe
          - platform: linux
            preset: "Linux/X11"
            extension: x86_64
          - platform: web
            preset: "Web"
            extension: html

    steps:
      - uses: actions/checkout@v4

      - uses: chickensoft-games/setup-godot@v2
        with:
          version: '4.5'
          include-templates: true

      - name: Import project
        run: godot --headless --path v1 --import

      - name: Export
        run: |
          mkdir -p build/${{ matrix.platform }}
          godot --headless --path v1 \
            --export-release "${{ matrix.preset }}" \
            ../build/${{ matrix.platform }}/MiniCozyRoom.${{ matrix.extension }}

      - uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.platform }}-build
          path: build/${{ matrix.platform }}

  release:
    needs: export
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            windows-build/*
            linux-build/*
            web-build/*
```

---

## 10. Godot 4.5 Specific Export Notes

### GL Compatibility Renderer

```
Our project uses GL Compatibility, which means:

Pros:
  ✓ Maximum hardware compatibility
  ✓ Works on old integrated GPUs
  ✓ Required for Web export (no Vulkan in browsers yet)
  ✓ Lower VRAM usage

Cons:
  ✗ No advanced lighting (GI, SSR, SSAO)
  ✗ No compute shaders
  ✗ Limited post-processing

For Relax Room: Perfect choice. We don't need 3D features.
```

### GDExtension Bundling (godot-sqlite)

```
Our project uses godot-sqlite, which is a GDExtension (native plugin).
This requires special handling during export:

The plugin provides platform-specific binaries:
  addons/godot-sqlite/bin/
  ├── libgdsqlite.windows.template_release.x86_64.dll
  ├── libgdsqlite.linux.template_release.x86_64.so
  ├── libgdsqlite.macos.template_release.framework/
  └── libgdsqlite.web.template_release.wasm32.wasm  (if available)

Export checklist:
  ✓ All platform .dll/.so/.dylib files included in PCK
  ✓ .gdextension file correctly references all platforms
  ✓ Test export on each target platform
  ✗ Web export may not support SQLite (check plugin status)

If web doesn't support SQLite:
  - Use feature tag: OS.has_feature("web")
  - Fallback to JSON-only persistence on web
  - Our project already has this fallback (JSON is primary)
```

### Export Troubleshooting

```
Common issues:

1. "No export template found"
   Fix: Editor → Export → Manage Templates → Download

2. "Resource not found" at runtime
   Fix: Check export filters — is the file included?
   Check: .gdextension, .json, .wav files in export list

3. Crash on launch (release build only)
   Fix: Test with debug template first
   Check: Are there debug-only code paths? (print statements in _process)

4. "Cannot open database" (SQLite)
   Fix: Ensure .dll/.so is included in export
   Check: .gdextension platform entries

5. Web build shows blank screen
   Fix: Check browser console (F12) for errors
   Check: CORS headers on hosting server
   Check: SharedArrayBuffer support (requires HTTPS + headers)
```

---

## 11. Summary: Our Project's Build Strategy

```
Current State:
  - Development in Godot 4.5 on Windows
  - CI runs on GitHub Actions (lint + test)
  - No automated export yet

Recommended Build Pipeline:

Phase 1 (Now):
  ✓ Local development with F5 in Godot
  ✓ CI linting and testing on push
  ✓ Manual export for testing

Phase 2 (Before release):
  □ Add automated export to CI (GitHub Actions)
  □ Export for Windows + Linux + Web
  □ Test godot-sqlite on all platforms
  □ Set up itch.io page

Phase 3 (Release):
  □ Tag version v1.0.0
  □ CI automatically builds all platforms
  □ Upload to itch.io via Butler
  □ Create installer for Windows (Inno Setup)
  □ Write credits/licenses screen
  □ Privacy policy (if Supabase is enabled)

Phase 4 (Post-release):
  □ Delta patches via itch.io Butler
  □ Save file migration for updates
  □ Consider Steam if there's demand
```

---

## 13. Troubleshooting Export — Problemi Comuni

### "Export template not found"

**Causa**: Non avete scaricato i template di esportazione per la versione corrente di Godot.

**Soluzione**:
1. Aprite Godot → `Editor → Manage Export Templates`
2. Cliccate "Download and Install" per la versione corrente
3. Attendete il download (~500 MB per tutti i template)
4. Riprovate l'export

**Se il download fallisce**: Scaricate manualmente i template da https://godotengine.org/download e importateli con "Install from File".

### godot-sqlite non funziona dopo l'export

**Causa**: Il GDExtension godot-sqlite richiede che i file binari nativi (.dll, .so, .dylib) siano inclusi nell'export.

**Soluzione**:
1. Verificate che `v1/addons/godot-sqlite/` contenga i binari per la piattaforma target:
   - Windows: `libgdsqlite.windows.template_release.x86_64.dll`
   - Linux: `libgdsqlite.linux.template_release.x86_64.so`
   - Web: `libgdsqlite.web.template_release.wasm32.wasm`
2. Nelle impostazioni Export, verificate che i filtri NON escludano `addons/`
3. Nella sezione "Resources" dell'export preset, assicuratevi che `*.gdextension` sia incluso

### HTML5: Schermo Nero dopo il Caricamento

**Cause comuni**:
1. **SharedArrayBuffer non supportato**: L'export HTML5 di Godot 4 richiede che il server invii gli header:
   ```
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Embedder-Policy: require-corp
   ```
   Soluzione: Usate un server locale che li supporta (vedi sezione 15)

2. **File .pck troppo grande**: Se il file `.pck` supera i 50 MB, il browser potrebbe non riuscire a caricarlo. Ottimizzate gli asset (sezione 14)

3. **WebGL non supportato**: Browser molto vecchi o configurazioni con WebGL disabilitato. Verificate su https://get.webgl.org/

### Windows Defender Blocca l'Eseguibile

**Causa**: Windows Defender segnala gli eseguibili non firmati (code-signed) come potenzialmente pericolosi.

**Soluzioni**:
1. **Per lo sviluppo**: Aggiungete la cartella di export alle eccezioni di Windows Defender
2. **Per la distribuzione**: Firmate l'eseguibile con un certificato di code signing (a pagamento, ~$200-400/anno)
3. **Alternativa gratuita**: Distribuite su itch.io con il loro launcher, che gestisce la trust chain

---

## 14. Ottimizzazione Dimensione Build

Il peso dell'eseguibile finale influisce su download, storage e tempi di avvio. Ecco come ridurlo.

### Audio: WAV vs OGG

| Formato | Dimensione (1 min musica) | Qualita' | Uso Consigliato |
|---------|--------------------------|----------|-----------------|
| WAV | ~10 MB | Lossless | Solo effetti sonori brevi (<5 sec) |
| OGG Vorbis | ~1 MB | Lossy (buona) | Musica, ambience, loop lunghi |
| MP3 | ~1 MB | Lossy (buona) | NON usare in Godot 4 (supporto limitato) |

**Azione**: Convertite TUTTE le tracce musicali in `v1/assets/audio/music/` da WAV a OGG Vorbis con qualita' 6 (bilanciamento dimensione/qualita'). Potete usare Audacity (gratuito) o FFmpeg:
```bash
# Converte tutti i WAV in OGG (qualita' 6)
for f in v1/assets/audio/music/*.wav; do
    ffmpeg -i "$f" -c:a libvorbis -q:a 6 "${f%.wav}.ogg"
done
```

### Texture Compression

Nelle impostazioni di Import di ogni texture (pannello Import in Godot):
- **Compress Mode**: "Lossless" per pixel art (mantiene la nitidezza dei pixel)
- **Filter**: "Nearest" (gia' impostato globalmente nel progetto)
- **Mipmaps**: OFF per 2D (le mipmap sono utili solo per il 3D)

### Feature Stripping (Riduzione Funzionalita')

Nelle impostazioni Export, disabilitate le funzionalita' non usate:
- **3D**: Disabilitate tutto (siamo un gioco 2D)
- **Navigation**: Disabilitate (non usiamo pathfinding con NavigationServer)
- **XR (VR/AR)**: Disabilitate
- **Advanced text server**: Se non usate lingue RTL (arabo, ebraico), potete usare il text server base

Questo puo' ridurre l'eseguibile di 5-15 MB.

---

## 15. Test Export Locale — Guida Passo Passo

### Export Windows (da Windows)

```text
1. Project → Export → Add → Windows Desktop
2. Configurate:
   - Export Path: una cartella fuori dal progetto (es. C:\Users\voi\Desktop\MCR_Export\)
   - Architecture: x86_64
   - Embed PCK: ON (crea un singolo .exe)
3. Cliccate "Export Project"
4. Navigate alla cartella e fate doppio click sull'eseguibile
5. Verificate:
   - [ ] Il gioco si avvia senza errori
   - [ ] La musica funziona
   - [ ] Il salvataggio funziona (decorate, chiudete, riaprite — decorazioni presenti?)
   - [ ] Nessun crash dopo 2 minuti di uso
```

### Export HTML5 + Test Locale

L'export web richiede un server HTTP per funzionare (non potete aprire il file .html direttamente).

```text
1. Project → Export → Add → Web
2. Configurate:
   - Export Path: cartella dedicata (es. export_web/)
   - Thread Support: ON (necessario per godot-sqlite)
3. Cliccate "Export Project"
4. Aprite un terminale nella cartella di export e avviate un server locale:
```

```bash
# Python 3 (installato di default su Linux/macOS)
cd path/to/export_web/
python3 -m http.server 8000

# Poi aprite nel browser: http://localhost:8000
```

**Nota importante**: Il server Python base NON invia gli header COOP/COEP necessari. Per un test completo, usate:

```bash
# Installate un server con supporto header (richiede Node.js)
npx http-server -p 8000 --cors -c-1 \
  -S -C cert.pem -K key.pem \
  --header "Cross-Origin-Opener-Policy: same-origin" \
  --header "Cross-Origin-Embedder-Policy: require-corp"
```

---

## 16. Inno Setup — Installer Windows Professionale

### Cos'e' Inno Setup

Inno Setup e' un tool gratuito per creare installer `.exe` per Windows. Trasforma
il gioco esportato da Godot in un installer professionale con:
- Wizard di installazione (schermata licenza, scelta cartella, progresso)
- Shortcut su Desktop e Start Menu
- Disinstallazione pulita dal Pannello di Controllo
- Compressione LZMA2 (riduce dimensione)

### Pre-requisiti

```
Per compilare su Windows:
  1. Scaricate Inno Setup da https://jrsoftware.org/isinfo.php
  2. Installate (include il compilatore ISCC.exe)
  3. Aprite il file .iss con Inno Setup Compiler
  4. Compile → il file Setup_MiniCozyRoom.exe viene generato

Per compilare su Linux (CI/CD):
  1. Installate WINE: sudo apt install wine
  2. Scaricate Inno Setup e installatelo con: wine innosetup-6.x.x.exe
  3. Compilate: wine ~/.wine/drive_c/.../ISCC.exe MiniCozyRoom.iss
```

### Script Inno Setup per Relax Room

```iss
; Relax Room — Inno Setup Script
; Genera un installer professionale per Windows

[Setup]
AppName=Relax Room
AppVersion=1.0.0
AppPublisher=IFTS Projectwork Team
AppPublisherURL=https://github.com/renanaugustomacena-ux/Projectwork-IFTS-Private
DefaultDirName={autopf}\MiniCozyRoom
DefaultGroupName=Relax Room
OutputDir=installer_output
OutputBaseFilename=Setup_MiniCozyRoom_v1.0.0
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
; PrivilegesRequired=lowest → l'utente NON ha bisogno di permessi admin
; Il gioco si installa nella cartella utente (AppData o Program Files)

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un'icona sul Desktop"; \
  GroupDescription: "Icone aggiuntive:"; Flags: unchecked

[Files]
; Tutti i file dalla cartella di export Godot
Source: "export\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
; Shortcut nel menu Start
Name: "{group}\Relax Room"; Filename: "{app}\MiniCozyRoom.exe"
; Shortcut opzionale sul Desktop
Name: "{autodesktop}\Relax Room"; Filename: "{app}\MiniCozyRoom.exe"; \
  Tasks: desktopicon

[Run]
; Opzione "Avvia Relax Room" alla fine dell'installazione
Filename: "{app}\MiniCozyRoom.exe"; \
  Description: "Avvia Relax Room"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Pulisci file generati a runtime (save, database, log)
Type: filesandordirs; Name: "{app}\*.log"
```

### Note sull'Icona

```
L'installer richiede un file .ico per l'icona di setup.
Per convertire un PNG in ICO:

Online: https://icoconvert.com/ (gratuito)
CLI: convert icon.png -resize 256x256 icon.ico (ImageMagick)
Godot: Esporta gia' l'icona nel .exe se configurata in Project Settings

Il file .ico deve contenere risoluzioni multiple:
  16x16, 32x32, 48x48, 64x64, 128x128, 256x256
```

### Code Signing (Opzionale ma Raccomandato)

```
PROBLEMA: Windows SmartScreen blocca eseguibili non firmati con un avviso
"Windows ha protetto il tuo PC" → scoraggia gli utenti.

SOLUZIONI:
1. Certificato a pagamento (~$200-400/anno)
   - Comodo, DigiCert, Sectigo
   - Firma con: signtool sign /f cert.pfx /p password MiniCozyRoom.exe

2. Self-signed (gratuito, NON elimina l'avviso ma lo riduce)
   - openssl + osslsigncode
   - Utile solo per sviluppo/testing

3. Distribuire via itch.io
   - Il launcher itch gestisce la trust chain
   - L'avviso SmartScreen non appare

Per il nostro progetto scolastico: opzione 3 (itch.io) e' la migliore.
```

---

## 17. Export Android — APK e AAB

### Differenza APK vs AAB

```
APK (Android Package):
  - File singolo installabile direttamente
  - Sideloading: copia sul telefono e installa
  - Test locale: adb install MiniCozyRoom.apk
  - Non ottimizzato per dimensione (contiene tutti gli asset)

AAB (Android App Bundle):
  - Formato richiesto dal Google Play Store
  - Google genera APK ottimizzati per ogni dispositivo
  - Non installabile direttamente (solo via Play Store)
  - Dimensione finale piu' piccola per l'utente

Per noi:
  - Sviluppo/test: APK (piu' semplice)
  - Distribuzione Play Store: AAB
```

### Pre-requisiti

```
1. JDK 17 (Java Development Kit)
   Ubuntu/Debian:
     sudo apt install openjdk-17-jdk
   Verifica:
     java -version → deve mostrare "17.x.x"

   IMPORTANTE: NON usare JDK 21+ (Godot non e' ancora compatibile)

2. Android SDK (via Android Studio o standalone)
   Metodo consigliato: installare Android Studio
     - Scaricate da https://developer.android.com/studio
     - Durante l'installazione, selezionate:
       - Android SDK Platform-Tools
       - Android SDK Build-Tools
       - Android SDK Platform (API 34+)
     - Nota il percorso SDK (es: ~/Android/Sdk)

   Metodo standalone (senza Android Studio):
     - Scaricate Command Line Tools da developer.android.com
     - sdkmanager "platform-tools" "build-tools;34.0.0" "platforms;android-34"

3. Export Templates Godot
   In Godot: Editor → Manage Export Templates → Download

4. Configurazione in Godot
   Editor → Editor Settings → Export → Android:
     - Java SDK Path: /usr/lib/jvm/java-17-openjdk-amd64
     - Android SDK Path: ~/Android/Sdk
```

### Creazione Keystore

```bash
# Debug keystore (per test locali — NON per distribuzione)
keytool -keyalg RSA -genkeypair -alias androiddebugkey \
  -keypass android -keystore debug.keystore -storepass android \
  -dname "CN=Android Debug,O=Android,C=US" -validity 9999

# Release keystore (per distribuzione — CONSERVARE AL SICURO!)
keytool -v -genkey -keystore minicozyroom-release.keystore \
  -alias minicozyroom -keyalg RSA -keysize 2048 -validity 10000

# Vi chiedera':
#   - Password keystore (scegliete una sicura, NON perdetela)
#   - Nome, organizzazione, citta', paese
#   - Password chiave (puo' essere uguale alla keystore password)
```

```
IMPORTANTE — Sicurezza Keystore:
  - Il release keystore identifica la vostra app per sempre
  - Se lo perdete, NON potete aggiornare l'app sul Play Store
  - NON committatelo nel repository Git
  - Salvate una copia in un luogo sicuro (USB, cloud privato)
  - Aggiungete *.keystore al .gitignore
```

### Configurazione Export Preset

```
In Godot: Project → Export → Add → Android

Impostazioni chiave:
  - Package → Unique Name: com.ifts.minicozyroom
  - Package → Name: Relax Room
  - Version → Code: 1 (incrementare ad ogni release)
  - Version → Name: 1.0.0
  - Architectures → arm64-v8a: ON (dispositivi moderni)
  - Architectures → armeabi-v7a: OFF (vecchi, non necessario)
  - Keystore → Debug: percorso al debug.keystore
  - Keystore → Release: percorso al release keystore
  - Permissions → Internet: ON (per Supabase, fase 4)

Filtri risorse:
  - Assicuratevi che *.json, *.gdextension siano inclusi
  - I binari .so per Android sono gia' nel nostro addon godot-sqlite
```

### godot-sqlite su Android

```
Il nostro plugin godot-sqlite include gia' i binari Android:

  addons/godot-sqlite/bin/
  ├── libgdsqlite.android.template_debug.arm64.so
  └── libgdsqlite.android.template_release.arm64.so

Il file .gdextension referenzia automaticamente questi binari.
Il database path user:// funziona su Android senza modifiche:
  user:// → /data/data/com.ifts.minicozyroom/files/

NON serve nessun permesso WRITE_EXTERNAL_STORAGE:
  il database e' nella cartella interna dell'app (sandboxed).
```

### Test su Dispositivo

```
Via USB (il metodo piu' veloce):
  1. Attivate "Opzioni sviluppatore" sul telefono
     (Impostazioni → Info telefono → tocca 7 volte su "Numero build")
  2. Attivate "Debug USB"
  3. Collegate il telefono via USB
  4. In Godot: Project → Export → Android → Export Project
  5. Selezionate il dispositivo nella lista
  6. Il gioco si installa e si avvia automaticamente

Via APK (senza cavo):
  1. Esportate come APK
  2. Copiate il file .apk sul telefono (email, cloud, USB)
  3. Aprite il file → "Installa da fonti sconosciute" → Installa

Via Emulatore:
  1. Android Studio → AVD Manager → Create Virtual Device
  2. Scegliete un dispositivo (es: Pixel 7, API 34)
  3. Esportate il gioco
  4. adb install -r MiniCozyRoom.apk
```

---

## 18. Checklist Pre-Release Professionale

### Preparazione

```
[ ] Versioning
    - Version string nel project.godot (es: 1.0.0)
    - Version code Android incrementato
    - SAVE_VERSION in save_manager.gd allineato

[ ] Icona e Branding
    - Icona applicazione in project.godot (boot/splash)
    - Icona .ico per Windows (256x256 embedded)
    - Icona adaptive per Android (foreground + background)
    - Nome applicazione corretto su tutte le piattaforme

[ ] Ottimizzazione Build
    - Audio: tracce musicali in OGG Vorbis (non WAV)
    - Texture: Lossless per pixel art, Nearest filter
    - Feature stripping: 3D disabilitato, XR disabilitato
    - Export mode: Release (non Debug) per distribuzione

[ ] Sicurezza
    - export_presets.cfg nel .gitignore (contiene password keystore)
    - *.keystore nel .gitignore
    - Nessuna service_role key Supabase nel codice client
    - Password hash con salt (non in chiaro)

[ ] Legale
    - File LICENZE/CREDITS in-game con tutti gli asset usati
    - Licenze asset rispettate (crediti, no redistribuzione)
    - Privacy Policy se raccogliete dati utente (email, Supabase)
    - GDPR: opzione per cancellare account e tutti i dati

[ ] Test Pre-Release
    - [ ] Windows: gioco si avvia, salva, carica, non crasha
    - [ ] Android: gioco si avvia, touch funziona, salva funziona
    - [ ] Web: gioco si carica, SQLite fallback a JSON
    - [ ] Save migration: carica save vecchio → migra correttamente
    - [ ] Fresh install: primo avvio → guest mode → tutto funziona
    - [ ] Uninstall + reinstall: dati utente preservati? (dipende dalla scelta)
```

### Dimensione Build Stimata

```
Componente               Dimensione stimata
─────────                ──────────────────
Godot runtime (.exe)     ~45 MB (Windows)
                         ~25 MB (Android, ARM64)
                         ~15 MB (Web, WASM)
Asset grafici (PCK)      ~15-25 MB (dipende da compressione)
Audio (se OGG)           ~2-4 MB (2 tracce)
godot-sqlite (.dll/.so)  ~3-5 MB
───────────────────────────────────────────
Totale Windows           ~65-80 MB
Totale Android APK       ~45-55 MB
Totale Web               ~25-40 MB
Installer (LZMA2)        ~35-45 MB (compresso)
```

---

*Study document for Relax Room — IFTS Projectwork 2026*
*Author: Renan Augusto Macena (System Architect & Project Supervisor)*

---

## Exercises

1. **Lab — Inno Setup installer.** Build a Windows installer for a simple Godot game, with custom icon, license, install directory.
2. **Lab — GitHub Actions CI.** Pipeline that exports Windows + Linux + Android on tag push.
3. **Stretch — macOS notarization.** Sign + notarize a Godot export for macOS distribution.

## Self-assessment

1. Why pin export templates version?
2. Inno Setup vs MSI: tradeoff.
3. AAB vs APK for Android.
4. CI/CD: minimum stages for game export pipeline.
5. Notarization: cost and frequency.

## Cross-links

- Module 10 — `GAME_DEV_PLANNING.md`: pre-release checklist.
- `00-CAPSTONE.md`: capstone requires shippable build.

## Local glossary

| Term | Definition |
|---|---|
| **Export template** | Godot binary used to package game per platform. |
| **Inno Setup** | Windows installer creator. |
| **AppImage** | Linux portable single-file binary. |
| **Notarization** | Apple cert verification for macOS apps. |
| **APK / AAB** | Android Package / App Bundle. |
| **CI/CD** | Continuous Integration / Continuous Deployment. |
| **Code signing** | Cryptographic signature on binary. |
