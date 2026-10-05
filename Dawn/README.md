# Building Dawn

This directory contains scripts that can be used to build Dawn for various platforms.
These scripts are used in CI to build a [static library artifact
bundle](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0482-swiftpm-static-library-binary-target-non-apple-platforms.md).
That is a bundle that contains static libraries for a number of different architectures
and platforms.

## Dawn and Chromium

Dawn does not have version numbers like most software libraries. This makes it hard to
decide what to build. Since Dawn is tightly linked to Chromium, we choose what git hash
of Dawn to build by matching it with a release of Chromium.

## Using the CI Scripts

If you wish to build a version of Dawn yourself, you can use these CI scripts as follows:

```bash
# Recommended Python setup
python3 -m venv .venv
pip3 install -r requirements.txt

# Determine the latest release of Chromium Canary and get the Dawn hash
# Write the data to dawn_version.json
./ci_build_dawn.py get-dawn-version

# Download the Dawn source matching the given hash
./ci_build_dawn.py get-source --hash cc0a37d660cef88a78a751b9fc1431be3d1ce2eb

# Build Dawn, running these commands on the appropriate platform
# Note that macosx builds both Intel and Arm
./ci_build_dawn.py build-target --target macosx
./ci_build_dawn.py build-target --target iphoneos
./ci_build_dawn.py build-target --target iphonesimulator

# Or on a Linux machine
./ci_build_dawn.py build-target --target linux

# Combine the builds into an archive bundle (all build products need to be in the same filesystem)
./ci_build_dawn.py bundle --chromium-version 142.0.7404.0 --dawn-hash cc0a37d660cef88a78a751b9fc1431be3d1ce2eb --bundle-name dawn_webgpu_chromium_142.0.7404.0_canary_cc0a37d660cef88a78a751b9fc1431be3d1ce2eb
```


## Android / Vulkan

Use Python 3.10+, CMake, Ninja and an Android NDK (API 29+). The Android
profile enables Vulkan and disables OpenGL ES, desktop GL and desktop backends.
The helper pins Dawn to the revision used by the checked-in Swift bindings:

```sh
export ANDROID_NDK_HOME=/path/to/android-ndk
python3 Dawn/build_android.py --arch arm64 --jobs 6
# Add --arch x86_64 to produce both variants.
export SWAN_LOCAL_DAWN=Dawn/dist/android.artifactbundle
export SWAN_RUNTIME_ONLY=1
swift build --swift-sdk aarch64-unknown-linux-android29 --target WebGPU
```

`SWAN_LOCAL_DAWN` is relative to the Swan package root. `SWAN_RUNTIME_ONLY=1`
uses checked-in native bindings and excludes generator tools and their
SwiftSyntax/SwiftFormat dependencies. Do not use it while regenerating bindings.
Original Dawn builds retain debug data; artifact copies are stripped.
