/* gbarun: a tiny headless GBA runner on top of libmgba, driven over stdin/stdout.
 *
 * It lets the Python tests in tests/emu/ play the real compiled ROM in a real emulator core:
 * press buttons, advance frames, read/write memory, take screenshots, use save states and
 * battery saves. No window, no audio, runs far faster than real time and is deterministic.
 *
 * Usage: gbarun ROM.gba [SAVE.sav]
 * One command per line; every command answers with exactly one line ("ok ..." or "err ...").
 *   f N            run N frames with the currently held keys
 *   k MASK         hold keys (GBA bitmask: A=1 B=2 SELECT=4 START=8 RIGHT=16 LEFT=32 UP=64 DOWN=128 R=256 L=512)
 *   r8|r16|r32 ADDR          read memory (hex or decimal address)
 *   w8|w16|w32 ADDR VALUE    write memory
 *   rb ADDR LEN              read LEN bytes, answered as hex
 *   shot PATH                write a PNG screenshot
 *   ss PATH / ls PATH        save / load an emulator save state
 *   reset                    reset the console (battery save is kept)
 *   quit
 */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba/core/serialize.h>
#include <mgba-util/png-io.h>
#include <mgba-util/vfs.h>

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void quietLog(struct mLogger* logger, int category, enum mLogLevel level, const char* format, va_list args) {
	(void) logger; (void) category; (void) level; (void) format; (void) args;
}

static struct mLogger sLogger = { .log = quietLog };

int main(int argc, char** argv) {
	if (argc < 2) {
		fprintf(stderr, "usage: gbarun ROM.gba [SAVE.sav]\n");
		return 2;
	}
	mLogSetDefaultLogger(&sLogger);
	struct mCore* core = mCoreFind(argv[1]);
	if (!core || !core->init(core)) {
		fprintf(stderr, "gbarun: cannot open %s as a GBA ROM\n", argv[1]);
		return 1;
	}
	mCoreInitConfig(core, NULL);
	unsigned width, height;
	core->desiredVideoDimensions(core, &width, &height);
	color_t* pixels = calloc(width * height, sizeof(color_t));
	core->setVideoBuffer(core, pixels, width);
	core->setAudioBufferSize(core, 2048);
	if (!mCoreLoadFile(core, argv[1])) {
		fprintf(stderr, "gbarun: failed to load %s\n", argv[1]);
		return 1;
	}
	if (argc > 2 && !mCoreLoadSaveFile(core, argv[2], false)) {
		fprintf(stderr, "gbarun: failed to open save %s\n", argv[2]);
		return 1;
	}
	core->reset(core);
	setvbuf(stdout, NULL, _IOLBF, 0);
	printf("ok ready %ux%u\n", width, height);

	char line[4096];
	unsigned long frames = 0;
	while (fgets(line, sizeof(line), stdin)) {
		char cmd[16] = "";
		char arg[3900] = "";
		unsigned long a = 0, b = 0;
		sscanf(line, "%15s", cmd);
		if (!strcmp(cmd, "f")) {
			sscanf(line, "%*s %lu", &a);
			for (unsigned long i = 0; i < a; ++i) {
				core->runFrame(core);
			}
			frames += a;
			printf("ok %lu\n", frames);
		} else if (!strcmp(cmd, "k")) {
			sscanf(line, "%*s %li", (long*) &a);
			core->setKeys(core, (uint32_t) a);
			printf("ok\n");
		} else if (!strcmp(cmd, "r8") || !strcmp(cmd, "r16") || !strcmp(cmd, "r32")) {
			sscanf(line, "%*s %li", (long*) &a);
			uint32_t v = !strcmp(cmd, "r8") ? core->busRead8(core, a) : !strcmp(cmd, "r16") ? core->busRead16(core, a) : core->busRead32(core, a);
			printf("ok %u\n", v);
		} else if (!strcmp(cmd, "w8") || !strcmp(cmd, "w16") || !strcmp(cmd, "w32")) {
			sscanf(line, "%*s %li %li", (long*) &a, (long*) &b);
			if (!strcmp(cmd, "w8")) {
				core->busWrite8(core, a, (uint8_t) b);
			} else if (!strcmp(cmd, "w16")) {
				core->busWrite16(core, a, (uint16_t) b);
			} else {
				core->busWrite32(core, a, (uint32_t) b);
			}
			printf("ok\n");
		} else if (!strcmp(cmd, "rb")) {
			sscanf(line, "%*s %li %li", (long*) &a, (long*) &b);
			printf("ok ");
			for (unsigned long i = 0; i < b; ++i) {
				printf("%02x", core->busRead8(core, a + i) & 0xFF);
			}
			printf("\n");
		} else if (!strcmp(cmd, "shot") || !strcmp(cmd, "ss") || !strcmp(cmd, "ls")) {
			if (sscanf(line, "%*s %3899[^\n]", arg) != 1) {
				printf("err missing path\n");
				continue;
			}
			bool ok = false;
			if (!strcmp(cmd, "ls")) {
				struct VFile* vf = VFileOpen(arg, O_RDONLY);
				if (vf) {
					ok = mCoreLoadStateNamed(core, vf, SAVESTATE_SAVEDATA);
					vf->close(vf);
				}
			} else {
				struct VFile* vf = VFileOpen(arg, O_CREAT | O_TRUNC | O_RDWR);
				if (vf && !strcmp(cmd, "ss")) {
					ok = mCoreSaveStateNamed(core, vf, SAVESTATE_SAVEDATA);
				} else if (vf) {
					png_structp png = PNGWriteOpen(vf);
					png_infop info = PNGWriteHeader(png, width, height);
					ok = PNGWritePixels(png, width, height, width, pixels);
					PNGWriteClose(png, info);
				}
				if (vf) {
					vf->close(vf);
				}
			}
			printf(ok ? "ok\n" : "err %s failed for %s\n", cmd, arg);
		} else if (!strcmp(cmd, "reset")) {
			core->reset(core);
			printf("ok\n");
		} else if (!strcmp(cmd, "quit")) {
			break;
		} else {
			printf("err unknown command\n");
		}
	}
	core->deinit(core);
	free(pixels);
	return 0;
}
