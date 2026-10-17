---
name: goldie
description: "Use when Dipesh wants App Store or Play Store screenshots / preview video for a mobile app in its code root. Not for desktop Agent-desk, not for marketing websites (use web-design)."
user-invocable: true
---

# Goldie — store screenshots (no git)

This file in DipeshPansuriya/agentic-skill-kit is the whole skill. Do not fetch a GitHub skill pack. The CLI is the npm package on PATH via npx (not a git checkout):

```
npx -y goldie@0 <command>
```

Needs Node 20+ and `ffmpeg` on PATH. **Windows/Linux: Android only** (`pixel-10-pro`). iPhone/iPad keys need macOS. Run from the **mobile app's code root**.

## Pipeline

0. If `goldie/goldie.config.ts` already exists, this is a follow-up — read it and the named `.argent/flows`; do not start over.
1. Target store from the repo (iOS / Android / ask if both). On this Windows PC default Play (`pixel-10-pro`) unless Dipesh is on a Mac.
2. Facts: app name, applicationId / bundle id, **Release** build (Debug paints overlays into marketing shots).
3. Walk the app; pick 4–5 screenshot scenes and a 3–4 clip preview story (App Store total 15–30 s).
4. Write flows under `.argent/flows/` (`store-01-…`, `store-preview-01-…`) and `goldie/goldie.config.ts`. Commit those; gitignore `goldie/out/`.
5. Every command needs `GOLDIE_CONFIG` (shell state does not persist):

```
GOLDIE_CONFIG=<code-root>/goldie/goldie.config.ts npx -y goldie@0 doctor
GOLDIE_CONFIG=... npx -y goldie@0 capture
GOLDIE_CONFIG=... npx -y goldie@0 frame
GOLDIE_CONFIG=... npx -y goldie@0 manifest
GOLDIE_CONFIG=... npx -y goldie@0 studio --no-open
GOLDIE_CONFIG=... npx -y goldie@0 preview && GOLDIE_CONFIG=... npx -y goldie@0 verify
```

Studio: http://localhost:4321. Fix broken flows with real `text:` / `id:` selectors, not guesses.

Play: `android.appPath` + `applicationId`, Pixel 10 Pro (or 9 Pro) AVD. Preview video is for YouTube (Play does not upload the file).

Arjun owns the run. Do not publish store assets until Dipesh says go.
