# Reproducible Linux build environment (also an option on Windows without setting up WSL).
#   docker build -t little-trainers .
#   docker run --rm -v "$PWD":/project little-trainers scripts/setup.sh --no-deps
#   docker run --rm -v "$PWD":/project little-trainers scripts/build.sh
# Note: game/tools and work/ hold binaries for the machine that built them. Use a separate clone
# for Docker, or delete game/tools/agbcc, work/.agbcc-stamp, work/gbarun and work/flips first.
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential binutils-arm-none-eabi git libpng-dev pkg-config python3 cmake zlib1g-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git config --global --add safe.directory '*'
WORKDIR /project
