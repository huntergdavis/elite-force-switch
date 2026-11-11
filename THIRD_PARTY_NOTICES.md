# Third-party source and license notices

This is an experimental source-only integration. These notices identify the
pinned inputs and known source-derived material; they do not grant rights to
retail game assets, resolve all file-level provenance, or establish that a
combined binary may be distributed. The repository does not include the
reference checkouts, game data, or a compiled game.

## VoyagerSP-Android

The build and tests refer to
[VoyagerSP-Android](https://github.com/imjustadudegamer/VoyagerSP-Android) at
`c73750361cfc22c1afb3a2c160fa9c5df57214db`. Its README identifies the engine
and port code as GPL version 2 and identifies `efgame/` as Raven-derived code
under the separate STEF Game Source License. Its engine license text is
reproduced in [licenses/GPL-2.0-SP.txt](licenses/GPL-2.0-SP.txt). The upstream
README credits id Software, ioquake3, lilium-voyager and Quake3e in the engine
lineage; consult the pinned upstream tree for individual notices and credits.

The UI patch scripts and tests contain or are derived from expressions,
identifiers and structures in the pinned SP game/UI sources. Their complete
file-level provenance and applicable rights remain under review. The
accompanying [STEF license transcription](licenses/STEF-Game-Source-License-transcription.txt)
was converted to plain text from the pinned `efgame/STEF Game Source License.doc`
with LibreOffice; it is provided for inspection, not represented as the
original document. The original document SHA-256 is
`167369d20489df17a0e0f823aec76ed44099204c5dd72dc2333f51790f6febc9`.
Consult the original in the pinned checkout and verify the transcription.

## VoyagerNX

The build and tests refer to [VoyagerNX](https://github.com/faithvoid/VoyagerNX)
at `649a63f6ee2a80c17a11b4ef35a42e6d2c7e0c6f`. Its README identifies the
engine as GPL version 2 or, at the recipient's option, any later version, and
states that its Elite Force game, cgame and UI sources are not included because
they have a non-free license. The pinned upstream license text is reproduced in
[licenses/GPL-2.0-VoyagerNX.txt](licenses/GPL-2.0-VoyagerNX.txt). Scripts
extract and adapt Switch platform, input and renderer code from that checkout;
consult its individual source notices and credits.

## Other dependencies and release status

The experimental linked build uses additional components including SDL2,
libnx, Switch graphics libraries and FFmpeg. Their exact retained components,
versions, build configuration, notices and corresponding-source obligations
have not been fully established. This source snapshot does not itself license
those components. See [bootstrap/PUBLIC_SOURCE_REVIEW.md](bootstrap/PUBLIC_SOURCE_REVIEW.md)
for the outstanding review, including Raven's terms, the CD-key-related change,
and the separately assessed distribution of a statically combined binary.
