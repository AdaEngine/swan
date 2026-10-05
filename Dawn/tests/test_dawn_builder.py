import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ci_targets import ci_target
from dawn_builder import Arch, OS, TargetConfig, cmake_flags


class CMakeFlagsTests(unittest.TestCase):
    def test_android_vulkan_profile_and_versioned_triples(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            toolchain = Path(directory) / "build/cmake/android.toolchain.cmake"
            toolchain.parent.mkdir(parents=True)
            toolchain.touch()
            with patch.dict(os.environ, {"ANDROID_NDK_HOME": directory}):
                target = ci_target("android", ["arm64"])
                flags = cmake_flags(target)
                self.assertIn("-DANDROID_ABI=arm64-v8a", flags)
                self.assertIn("-DANDROID_PLATFORM=android-29", flags)
                self.assertIn("-DDAWN_ENABLE_VULKAN=ON", flags)
                self.assertIn("-DDAWN_ENABLE_OPENGLES=OFF", flags)
                self.assertIn("aarch64-unknown-linux-android29", target.triples())
                self.assertNotIn("aarch64-unknown-linux-android28", target.triples())
                with self.assertRaisesRegex(ValueError, "separately"):
                    cmake_flags(ci_target("android", ["arm64", "x86_64"]))

    def test_windows_targets_use_visual_studio_18_generator(self) -> None:
        for arch in ("x86_64", "arm64"):
            with self.subTest(arch=arch):
                target_config = ci_target("windows", [arch])

                self.assertEqual(target_config.build_tool, "Visual Studio 18 2026")

    def test_linux_build_disables_dawn_cpp_modules(self) -> None:
        target_config = TargetConfig(
            os=OS.LINUX,
            arch=[Arch.X86_64],
        )

        flags = cmake_flags(target_config)

        self.assertIn("-DDAWN_SUPPORTS_CXX_MODULES=OFF", flags)

    def test_ios_build_passes_host_protoc_to_cmake(self) -> None:
        target_config = TargetConfig(
            os=OS.IPHONE,
            arch=[Arch.ARM64],
            sdk="iphoneos",
        )

        with patch("dawn_builder.find_sdk_path", return_value="/path/to/iphoneos.sdk"):
            with patch("dawn_builder.shutil.which", return_value="/opt/homebrew/bin/protoc"):
                flags = cmake_flags(target_config)

        self.assertIn("-DPROTOC_EXECUTABLE=/opt/homebrew/bin/protoc", flags)

    def test_ios_build_requires_host_protoc(self) -> None:
        target_config = TargetConfig(
            os=OS.IPHONE,
            arch=[Arch.ARM64],
            sdk="iphoneos",
        )

        with patch("dawn_builder.find_sdk_path", return_value="/path/to/iphoneos.sdk"):
            with patch("dawn_builder.shutil.which", return_value=None):
                with self.assertRaisesRegex(FileNotFoundError, "Host protoc"):
                    cmake_flags(target_config)


if __name__ == "__main__":
    unittest.main()
