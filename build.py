#!/usr/bin/env python3
"""Build the Android application and collect distributable artifacts."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
ANDROID_DIR = PROJECT_DIR / "xnotes-android"
if not (ANDROID_DIR / "gradlew").exists():
    ANDROID_DIR = PROJECT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compile the Android application and copy artifacts to an output folder."
    )
    parser.add_argument(
        "variant",
        choices=("debug", "release"),
        nargs="?",
        default="release",
        help="Build variant (default: release).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_DIR / "output",
        help="Destination folder for generated APK/AAB files (default: ./output).",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep existing files in the output folder instead of cleaning it first.",
    )
    parser.add_argument(
        "--java-home",
        type=Path,
        help="JDK to use for Gradle (JDK 17-24; otherwise JAVA_HOME is used).",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=2,
        help="Maximum number of Gradle workers (default: 2).",
    )
    parser.add_argument(
        "--heap-size",
        default="1536m",
        help="Gradle daemon heap size (default: 1536m).",
    )
    return parser.parse_args()


def java_major(java_home: Path | None) -> int | None:
    java = (java_home / "bin" / "java") if java_home else Path("java")
    try:
        result = subprocess.run(
            [str(java), "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    version_line = next(
        (line for line in (result.stderr + result.stdout).splitlines() if "version" in line),
        "",
    )
    match = re.search(r'"(\d+)(?:\.\d+)?', version_line)
    return int(match.group(1)) if match else None


def validate_environment(java_home: Path | None) -> bool:
    major = java_major(java_home)
    if major is None:
        print("JDK introuvable. Configurez JAVA_HOME ou utilisez --java-home.", file=sys.stderr)
        return False
    if not 17 <= major <= 24:
        print(
            f"JDK {major} détecté. Ce projet nécessite un JDK entre 17 et 24; "
            "JDK 25 n'est pas compatible avec Kotlin/Gradle utilisé.",
            file=sys.stderr,
        )
        return False

    local_properties = ANDROID_DIR / "local.properties"
    sdk_configured = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk_configured and not local_properties.exists():
        print(
            "Android SDK introuvable. Configurez ANDROID_HOME/ANDROID_SDK_ROOT "
            f"ou créez {local_properties} avec sdk.dir.",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    args = parse_args()
    gradle_wrapper = ANDROID_DIR / ("gradlew.bat" if sys.platform == "win32" else "gradlew")
    if not gradle_wrapper.exists():
        print(f"Gradle wrapper introuvable: {gradle_wrapper}", file=sys.stderr)
        return 1
    java_home = args.java_home.expanduser().resolve() if args.java_home else None
    if java_home:
        if not (java_home / "bin" / "java").exists():
            print(f"JDK introuvable dans --java-home: {java_home}", file=sys.stderr)
            return 1
    if not validate_environment(java_home):
        return 1

    output_dir = args.output.expanduser().resolve()
    if output_dir in {PROJECT_DIR.resolve(), ANDROID_DIR.resolve()}:
        print(
            "--output doit désigner un dossier dédié, différent de la racine du projet.",
            file=sys.stderr,
        )
        return 1
    if not args.keep_output and output_dir.exists():
        for child in output_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)

    task = f":app:assemble{args.variant.capitalize()}"
    print(f"Compilation de la variante {args.variant}...", flush=True)
    try:
        environment = os.environ.copy()
        if java_home:
            environment["JAVA_HOME"] = str(java_home)
            environment["PATH"] = f"{java_home / 'bin'}{os.pathsep}{environment['PATH']}"
        subprocess.run(
            [
                str(gradle_wrapper),
                "--no-daemon",
                f"--max-workers={args.max_workers}",
                f"-Dorg.gradle.jvmargs=-Xmx{args.heap_size} -Dfile.encoding=UTF-8",
                "-Pkotlin.compiler.execution.strategy=in-process",
                task,
            ],
            cwd=ANDROID_DIR,
            env=environment,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f"La compilation a échoué (code {error.returncode}).", file=sys.stderr)
        return error.returncode

    variant_name = args.variant.lower()
    artifacts = sorted(
        artifact
        for pattern in ("*.apk", "*.aab")
        for artifact in (ANDROID_DIR / "app" / "build" / "outputs").rglob(pattern)
        if variant_name in {part.lower() for part in artifact.parts}
    )
    if not artifacts:
        print("Aucun APK ou AAB n'a été produit.", file=sys.stderr)
        return 1

    for artifact in artifacts:
        destination = output_dir / artifact.name
        shutil.copy2(artifact, destination)
        print(f"Artefact copié: {destination}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
