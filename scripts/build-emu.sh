#!/usr/bin/env bash
# Build the headless emulator runner used by the emulator tests:
#   1. fetch mGBA (MPL-2.0) at a pinned release into work/mgba and build a minimal static core
#      (no GUI, no ffmpeg, no audio/video front end), so tests do not depend on a system mGBA
#   2. compile tools/gbarun.c against it into work/gbarun
. "$(dirname "$0")/lib.sh"
MGBA_TAG=0.10.5
need git cmake cc
mkdir -p "$WORK"
if [ ! -d "$WORK/mgba/.git" ]; then
  say "Fetching mGBA $MGBA_TAG"
  git clone --quiet --depth 1 --branch "$MGBA_TAG" https://github.com/mgba-emu/mgba.git "$WORK/mgba"
fi
build="$WORK/mgba/build-headless"
if [ ! -f "$build/libmgba.a" ]; then
  say "Building libmgba (static, headless)"
  cmake -S "$WORK/mgba" -B "$build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DBUILD_SHARED=OFF -DBUILD_STATIC=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF -DBUILD_LIBRETRO=OFF \
    -DBUILD_PERF=OFF -DBUILD_TEST=OFF -DBUILD_SUITE=OFF -DBUILD_EXAMPLE=OFF -DBUILD_PYTHON=OFF \
    -DUSE_FFMPEG=OFF -DUSE_DISCORD_RPC=OFF -DUSE_EDITLINE=OFF -DUSE_GDB_STUB=OFF -DUSE_DEBUGGERS=OFF \
    -DUSE_LUA=OFF -DUSE_SQLITE3=OFF -DUSE_ELF=OFF -DUSE_LIBZIP=OFF -DUSE_MINIZIP=OFF -DUSE_LZMA=OFF \
    -DUSE_EPOXY=OFF -DBUILD_GL=OFF -DBUILD_GLES2=OFF -DBUILD_GLES3=OFF -DUSE_PNG=ON -DUSE_ZLIB=ON \
    -DM_CORE_GB=OFF -DENABLE_SCRIPTING=OFF >"$WORK/mgba-build.log" 2>&1 \
    && cmake --build "$build" --target mgba -j"$JOBS" >>"$WORK/mgba-build.log" 2>&1 \
    || die "mGBA build failed, see work/mgba-build.log"
fi
png_flags="$(pkg-config --cflags --libs libpng)"
if [ "$(uname -s)" = "Darwin" ]; then png_flags="$png_flags -framework CoreFoundation -framework Foundation"; fi
# shellcheck disable=SC2086
cc -O2 -Wall -Wextra -I"$WORK/mgba/include" -I"$build/include" "$ROOT/tools/gbarun.c" "$build/libmgba.a" \
  $png_flags -lz -lm -o "$WORK/gbarun" 2>"$WORK/gbarun-build.log" \
  || { cat "$WORK/gbarun-build.log"; die "could not build gbarun"; }
echo "built work/gbarun (mGBA $MGBA_TAG core)"
