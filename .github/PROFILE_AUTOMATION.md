# Profile automation setup

The contribution visuals use two token levels:

- `GITHUB_TOKEN` is the automatic repository-scoped fallback. It can update this repository, but it normally sees only public profile data.
- `PROFILE_TOKEN` is an optional repository secret owned by `DzCodeProgrammer`. It lets the snake, space shooter, and generated charts read the same contribution calendar that the profile owner can see.

## Required one-time setup for private contributions

1. Open GitHub **Settings → Developer settings → Personal access tokens → Tokens (classic)**.
2. Generate a short-lived token for this profile automation with the `read:user` scope. Do not grant write scopes.
3. Open this repository's **Settings → Secrets and variables → Actions**.
4. Create a repository secret named `PROFILE_TOKEN` and paste the token.
5. On the profile page, open **Contribution settings** and enable **Private contributions** if anonymized private totals should also be visible publicly.
6. Manually run these workflows once:
   - `Generate Contribution Snake`
   - `Update Space Shooter Game`
   - `Generate Profile Charts`

If `PROFILE_TOKEN` is missing or expires, every workflow falls back safely to `GITHUB_TOKEN`; however, private contribution totals can disappear from generated visuals. Rotate the token periodically and never put its value in the repository, workflow YAML, logs, or README.

## Schedule and ownership

| Workflow | Output | Schedule (UTC) |
| --- | --- | --- |
| Generate Contribution Snake | `output` branch SVG files | 01:00 daily |
| Generate Profile Charts | `assets/` charts and contribution summary | 01:30 daily |
| Update Space Shooter Game | `game.gif` | 02:15 daily |
| Update Profile Activity | README public activity section | Every six hours |

The workflows that commit to `main` share one concurrency group, so they cannot push over one another. The snake is the only workflow allowed to publish contribution files to the `output` branch.
