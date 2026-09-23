# Haulwise

Demo fleet platform used for a Scrutora walkthrough. Rules for anyone (human or Claude Code) working in this repo:

1. No comments that hint at seeded issues.
2. The answer key lives outside this repo, at `../haulwise_answer_key.md`.
3. Synthetic data only: Faker `en_IN`, generated phone numbers, placeholder avatars, ffmpeg-generated clips. No real faces.
4. No real brand names or UI. Tenants: `Aravalli Cement`, `Konkan Foods`.
5. `docker compose up` must run everything within 2 minutes.
6. Branches: `main` carries the seeded issues, `compliant` carries one fix commit per issue.

See `haulwise_techspec.md` in this repo root for the full spec this app was built from.
