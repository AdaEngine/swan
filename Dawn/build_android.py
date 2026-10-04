#!/usr/bin/env python3
"""Build a pinned Dawn Vulkan library and its SwiftPM Android artifact bundle."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
from ci_targets import ci_target
from dawn_builder import cmake_flags

DAWN_REVISION = "19696dd088b8ed5804e2f02a8f83f5afdb3e99e3"
CHROMIUM_VERSION = "148.0.7778.97"
ROOT = Path(__file__).resolve().parent

def run(args):
    subprocess.run([str(value) for value in args], check=True)

def build(architectures, jobs):
    source = ROOT/"dawn_source"
    if not (source/"CMakeLists.txt").exists():
        source.mkdir(parents=True, exist_ok=True)
        run(["git","init",source])
        run(["git","-C",source,"remote","add","origin","https://dawn.googlesource.com/dawn"])
        run(["git","-C",source,"fetch","--depth","1","origin",DAWN_REVISION])
        run(["git","-C",source,"checkout","--detach","FETCH_HEAD"])
    actual = subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
    if actual != DAWN_REVISION:
        raise RuntimeError(f"Dawn source must match the Swan bindings: expected {DAWN_REVISION}, found {actual}")
    bundle = ROOT/"dist/android.artifactbundle"
    bundle.mkdir(parents=True,exist_ok=True)
    variants = []
    for arch in architectures:
        config = ci_target("android",[arch])
        output = ROOT/"builds"/str(config)
        run(["cmake","-S",ROOT,"-B",output/"out","-G","Ninja",*cmake_flags(config),f"-DPython3_EXECUTABLE={sys.executable}"])
        run(["cmake","--build",output/"out","--target","webgpu_dawn","--parallel",jobs])
        run(["cmake","--install",output/"out","--prefix",output/"install"])
        target = bundle/str(config)
        target.mkdir(parents=True,exist_ok=True)
        shutil.copy2(output/"install/lib/libwebgpu_dawn.a",target/"libwebgpu_dawn.a")
        shutil.copytree(output/"install/include",target/"include",dirs_exist_ok=True)
        ndk=Path(os.environ["ANDROID_NDK_HOME"])
        hosts=list((ndk/"toolchains/llvm/prebuilt").glob("*"))
        run([hosts[0]/"bin/llvm-strip","--strip-debug",target/"libwebgpu_dawn.a"])
        variants.append({"path":f"{config}/libwebgpu_dawn.a","staticLibraryMetadata":{"headerPaths":[f"{config}/include"]},"supportedTriples":config.triples()})
    shutil.copy2(source/"src/dawn/dawn.json",bundle/"dawn.json")
    (bundle/"info.json").write_text(json.dumps({"schemaVersion":"1.0","artifacts":{"dawn_webgpu":{"type":"staticLibrary","version":CHROMIUM_VERSION,"variants":variants}}},indent=2))
    (bundle/"dawn_version.json").write_text(json.dumps({"dawn_hash":DAWN_REVISION,"chromium_version":CHROMIUM_VERSION},indent=2))
    print(f"SWAN_LOCAL_DAWN={bundle.relative_to(ROOT.parent)}")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch",action="append",choices=["arm64","x86_64"])
    parser.add_argument("--jobs",type=int,default=6)
    args=parser.parse_args()
    build(args.arch or ["arm64"],str(args.jobs))
