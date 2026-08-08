## 2026-08-07T22:19:16Z
<USER_REQUEST>
You are a Worker subagent (Worker 1).
Working directory: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_worker_m1_m2_1
Original Request Path: /Users/rmanaloto/agy-graphify-research/.agents/ORIGINAL_REQUEST.md
PROJECT.md Path: /Users/rmanaloto/agy-graphify-research/.agents/teamwork_preview_orchestrator_2/PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Task (Milestones 1 & 2):
1. Create canonical `raw/` multi-modal directory layout at workspace root:
   - `raw/papers/.gitkeep` (for `.pdf` academic papers & books)
   - `raw/media/.gitkeep` (for `.mp4`, `.mp3`, `.m4a`, `.wav` video/audio)
   - `raw/web/.gitkeep` (for scraped web pages and HTML/markdown articles)
   - `raw/images/.gitkeep` (for `.png`, `.jpg`, `.svg` images & diagrams)

2. Update `config/sources.json` to version 1.1.0:
   ```json
   {
     "version": "1.1.0",
     "updated_at": "2026-08-07T22:18:00Z",
     "manifest_source": "graphify-out/extended_repo_manifest.json",
     "sources": {
       "git_repositories": "repos/",
       "raw_papers": "raw/papers/",
       "raw_media": "raw/media/",
       "raw_web": "raw/web/",
       "raw_images": "raw/images/"
     }
   }
   ```

3. Run `uv run pytest` to verify test suite remains passing.
4. Report changes and verification results in `.agents/teamwork_preview_worker_m1_m2_1/handoff.md` and `.agents/teamwork_preview_worker_m1_m2_1/progress.md`.
Send a message back when done.
</USER_REQUEST>
