# Tag After School Android launcher (experimental)

This repository builds an Android-labeled APK using the open-source **gmRunner** runtime. It is not Winlator and does not bundle or redistribute the game's copyrighted files.

## Build an APK
1. Open the repository's **Actions** tab.
2. Choose **Build Tag After School Android launcher**.
3. Press **Run workflow** on the `main` branch (or wait for the push-triggered build).
4. When it succeeds, download the artifact named `TagAfterSchool-Android-build`.

The artifact contains:
- `TagAfterSchool-Android.apk`
- `Tag-After-School-folder-template.zip` (contains a folder with `gmrunner.ini`)
- `INSTALL.txt`

## Install and add game files
1. Install the APK.
2. Extract the folder-template ZIP to internal storage `/storage/emulated/0/gmrunner/`.
3. Copy the game files you own into the new `Tag After School` folder. Ensure `data.win` is directly inside it; keep accompanying files beside it.
4. Open the launcher and grant file access if requested.
5. Tap the game entry to launch.

## Current status / caveat
This is an **experimental runtime port**. We have not yet verified boot, menu interactions, audio, touchscreen behavior, or gameplay on an Android device for this particular game. The supplied Windows archive includes `data.win`, the Windows executable, `Text.csv`, and `options.ini`. If it fails, share the generated `gmrunner.log` and a screenshot so compatibility problems can be addressed.

The workflow checks out upstream gmRunner at its current default branch and builds an ARM64 debug APK. Upstream changes may require workflow adjustments.
