---
name: git-commit
description: Use when creating git commits — writing or rewording a commit message, splitting staged work into commits, amending, or preparing a branch for review (e.g. "commit this", "コミットして", "コミットを分けて", "commit message"). Enforces the house convention: prefix-tagged subjects (feat/fix/docs/refactor/chore/revert), a 50-character noun-phrase summary with no trailing period, What in the subject and Why in the body, and revert-safe commit granularity. Do NOT use for branch strategy, tagging, or PR review workflow questions.
---

# Git Commit Convention

House rules for how commits are split and how their messages are written.

## Commit granularity

Decide the split with these questions, in order:

- **Can this commit be reverted on its own?** A commit that leaves the tree unbuildable after `git revert` is too small or badly cut.
- **Does it review cleanly?** When a branch touches a lot, split so each commit carries one concern. Never pack unrelated concerns into one commit.
- **Is there a clear task unit?** A TODO item or a single bug fix is one commit.
- **Is it cross-cutting?** Shared or repo-wide changes get their own commit per purpose (e.g. a formatting sweep is one commit, separate from behaviour changes).

Typical split for one screen/feature:

```
○○画面のフロント部分を製造
○○画面のバックエンド部分を製造      (further split per sub-feature if large)
○○画面の表示バグ修正
○○ロジックのエラーハンドリング漏れを修正
現行資産の設計ドキュメントを新規追加
フォーマット漏れの一括適用
```

## Message format

```
<prefix>: <subject, <=50 chars, noun phrase, no trailing period>

<body: why, background, details — wrap at ~72 chars>

<issue/ticket refs, e.g. #1>
```

### Prefix

Required. Child entries are optional refinements — use them when they say more than the parent.

| Prefix | Use for |
|--------|---------|
| `feat` | New feature |
| `test` | Adding or fixing tests (under `feat`) |
| `fix` | Bug fix |
| `docs` | Adding or updating documentation |
| `refactor` | Code change that is neither a feature nor a bug fix |
| `perf` | Performance improvement (under `refactor`) |
| `remove` | Deleting code (under `refactor`) |
| `chore` | Everything else — build config, CI, tooling |
| `ci` | CI config files and scripts (under `chore`) |
| `build` | Build config and dependency changes (under `chore`) |
| `revert` | Reverting a commit |

### Subject line

- **Keep it within 50 characters** so it never wraps in `git log --oneline` or the GitHub UI.
- **No trailing period** (日本語では句点「。」も不要).
- **Write a noun phrase** — 体言止め. Drop verb endings like 「〜した」「〜する」: 「ログイン画面のバリデーション追加」, not 「ログイン画面のバリデーションを追加した」. In English this means a noun-phrase summary of the change, not a sentence.
- **State What, not How.** Details, background and rationale go in the body from line 2 onward.

### Body

- Separate from the subject with a blank line.
- Explain why the change was needed and anything a reviewer cannot read off the diff.
- Optional for a self-evident one-liner; expected when the change carries a decision.

### Issue references

When the project is tied to issues or tickets, put the number in the body (`#1`, `REDMINE-123`) — not in the subject, where it eats into the 50 characters.

## Message language

Match the repository. Run `git log --oneline -20` before writing the first commit in an unfamiliar repo and follow what is already there — Japanese repo, Japanese message; English repo, English message. Do not mix languages within one repository.

The 50-character limit is measured against Japanese text; for English, aim for the same visual length (roughly 50 characters, ~7 words).

## Workflow

1. `git status` and `git diff` (plus `git diff --staged`) to see the full change.
2. `git log --oneline -20` to pick up the repository's message language and style.
3. Group the changes into revert-safe, single-concern commits; stage each group with `git add <paths>` and commit it before moving to the next.
4. Write the message per the format above, then verify with `git log -1 --stat` that the commit contains exactly what was intended.

Before submitting a PR, tidy the history with `git rebase -i` so each commit follows these rules.

## Examples

```
feat: ユーザー登録画面のバリデーション追加

必須項目とメールアドレス形式のチェックをフロント側で実施する。
サーバー側チェックは既存のため変更なし。

#42
```

```
fix: 一覧画面で0件時にエラーとなる不具合の修正

検索結果が0件の場合に配列の先頭参照でNPEが発生していた。

#57
```

```
chore: CIのNode.jsバージョンを20に更新
```

Anti-patterns:

- `修正` — What is missing.
- `feat: ログイン機能を追加しました。` — 体言止めでない、句点あり.
- `feat: #42 ユーザー登録画面のバリデーション追加とエラーメッセージ文言の見直しとテスト追加` — over 50 chars, issue number in the subject, multiple concerns in one commit.
