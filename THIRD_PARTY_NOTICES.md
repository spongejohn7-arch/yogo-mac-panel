# Third-party notices and provenance

## rossgpt/yogo

- Upstream: https://github.com/rossgpt/yogo
- Revision: `ba646df545c4ae0c61623deebe4819d4626199cc`
- Copyright (c) 2026 rossgpt
- License: MIT; the complete, unmodified notice is included in
  [THIRD_PARTY_LICENSES/rossgpt-yogo-MIT.txt](THIRD_PARTY_LICENSES/rossgpt-yogo-MIT.txt).

This is an independent companion UI, not an official release or a claim of
ownership over the upstream driver. It imports upstream USB HID communication,
frame/color helpers, the small Latin font, and the original simple-status effects.
The installation script downloads the pinned upstream version as a dependency.
The upstream source tree and its Git history are not republished here.

The Chinese browser UI, local HTTP controller, read-only Codex event follower,
robot/garden/space pixel designs, launcher, packaging and their tests are additions
prepared for this project with AI assistance. The root MIT license applies to
these additions. It does not replace any third-party copyright notice.

## Other installed dependencies

`hid`, `Pillow` and `psutil` are installed from PyPI; HIDAPI is installed separately
through Homebrew. Their code/binaries are not included in this source repository.
Their original licenses remain applicable. Redistributing a bundled app or runtime
requires including the licenses for everything actually bundled; this source-only
release is not such a bundle.

YogoDot by Wednesque inspired the initial exploration. This repository does not
include its source, UI, artwork, fonts or Windows binaries.

ATK, YOGO, Codex and OpenAI names identify compatible products. This community
project is not affiliated with or endorsed by their owners or upstream authors.
