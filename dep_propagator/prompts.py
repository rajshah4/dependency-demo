from __future__ import annotations

from .config import RepoTarget, WorkflowConfig


PROMPT_TEMPLATE = """You are working in the selected repository `{selected_repository}` on branch `{selected_branch}`.

Goal: propagate an upstream dependency update from `{source_repo}` into this direct dependent repository by making the smallest correct downstream change set and opening exactly one pull request.

Constraints:
- Only update this repository.
- Keep changes minimal and focused on the dependency update plus required compatibility fixes.
- Do not make unrelated refactors or formatting-only changes.
- Do not modify unrelated files.
- If a validation command fails because the upstream change requires a small code fix, make only the smallest working fix.
- If you cannot complete the PR, explain the blocker clearly in the final message.

Upstream change:
- Dependency: `{dependency_name}`
- Previous version: `{old_version}`
- New version: `{new_version}`
- Summary: {upstream_summary}

Suggested working branch:
- `{branch_name}`

Expected PR title:
- `{pr_title}`

Repository hints:
{dependency_hints}

Repository-specific instructions:
{update_instructions}

Validation commands:
{validation_commands}

Additional context:
{extra_context}

Required steps:
1. Inspect the repository and confirm where `{dependency_name}` is referenced.
2. Create a branch named `{branch_name}` from `{selected_branch}`.
3. Update the dependency reference to the new upstream version.
4. Apply only the minimal code changes needed to keep the repository working.
5. Run the validation commands listed above, if any.
6. Commit only the relevant files.
7. Open a pull request targeting `{pr_base_branch}`.
8. Use a PR description that explains:
   - what changed upstream
   - what changed downstream
   - why the update was needed
   - which validation commands were run and their result
9. In your final message, include:
   - branch name
   - pull request URL
   - files changed
   - validation summary
   - any blocker if the PR could not be created
"""


def _as_bullets(items: list[str], *, fallback: str) -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def render_prompt(config: WorkflowConfig, repo: RepoTarget, branch_name: str, pr_title: str) -> str:
    old_version = config.upstream_change.old_version or "not specified"
    return PROMPT_TEMPLATE.format(
        selected_repository=repo.selected_repository,
        selected_branch=repo.selected_branch,
        source_repo=config.source_repo,
        dependency_name=config.dependency_name,
        old_version=old_version,
        new_version=config.upstream_change.new_version,
        upstream_summary=config.upstream_change.summary,
        branch_name=branch_name,
        pr_title=pr_title,
        dependency_hints=_as_bullets(
            repo.dependency_hints,
            fallback="Search the repository for dependency declarations and lockfiles before changing anything.",
        ),
        update_instructions=_as_bullets(
            repo.update_instructions + config.upstream_change.usage_notes,
            fallback="No extra instructions beyond making the dependency update and any minimal compatibility fix.",
        ),
        validation_commands=_as_bullets(
            repo.validation_commands,
            fallback="No validation commands were provided; run a lightweight relevant check only if obvious.",
        ),
        extra_context=_as_bullets(
            repo.extra_context,
            fallback="No additional repository context was provided.",
        ),
        pr_base_branch=repo.pr_base_branch or repo.selected_branch,
    )
