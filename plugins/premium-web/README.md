# premium-web

A Claude Code skill for building (and redesigning) premium web pages. Every section gets a drawn explanatory visual, the page gets one signature "wow" moment, and a calibrated critic, not the builder, decides when it is done.

Contents: rubric, wow ideation, genre-escape and verification references; scripts for screenshots, Lighthouse, saturation and the critic; an optional image-generation MCP server (`skills/premium-web/mcp/imagegen`).

Image keys are read through [vaultlet](https://github.com/anhermon/sealref) refs only; set `IMAGEGEN_VAULT_GROUP` to your group. Never paste keys into config.

The skeleton ships Hanken Grotesk (SIL OFL 1.1, licence in `assets/skeleton/fonts/`) as a placeholder face. Application and tool UIs are in scope (see SKILL.md "Application and tool UIs"); a gate that cannot run is reported UNVERIFIED, never pass.
