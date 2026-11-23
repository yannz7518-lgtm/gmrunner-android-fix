# Tag After School Android launcher (experimental)

This repository builds an Android-labeled APK using the open-source **gmRunner** runtime. It is not Winlator and does not bundle or redistribute the game's copyrighted files.

## Build an APK
1. Open the repository's **Actions** tab.
2. Choose **Build Tag After School Android launcher**.
3. Press **Run workflow** on the `main` branch.
4. When it succeeds, download the artifact named `TagAfterSchool-Android-build`.

The artifact contains the APK and a small setup template.

## Install and add game files
1. Install `TagAfterSchool-Android.apk`.
2. Extract the game files you own into `/storage/emulated/0/gmrunner/Tag After School/`.
3. Ensure `data.win` is directly inside that folder (keep any accompanying files there too).
4. Open the launcher and grant the requested file access.
5. Tap the game entry to start.

## Current status / caveat
This is an **experimental runtime port**. We have not yet verified boot, menu interactions, audio, touchscreen behavior, or gameplay on an Android device for this particular game. The Windows archive currently available includes `data.win`, the Windows executable, `Text.csv`, and `options.ini`. If it fails, share the generated `gmrunner.log` and a screenshot so compatibility problems can be addressed.

The workflow checks out the upstream gmRunner source at its current default branch and builds an ARM64 debug APK. Upstream changes may require workflow adjustments.
