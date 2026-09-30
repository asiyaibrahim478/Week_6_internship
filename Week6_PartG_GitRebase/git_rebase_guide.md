# Week 6 — Part G: Cleaning History with Interactive Rebase

## What is Interactive Rebase?
Interactive Rebase (`git rebase -i HEAD~N`) allows developers to rewrite the local commit history on their private feature branch before opening a Pull Request.

---

## 🧹 Key Capabilities
1. **Squash (`s` / `squash`):** Combines multiple intermediate WIP commits (`"wip"`, `"fix typo"`, `"try again"`) into a single, cohesive commit with a clean title and body.
2. **Reword (`r` / `reword`):** Edits and standardizes commit messages to follow project conventions (`feat:`, `fix:`, `docs:`).
3. **Drop (`d` / `drop`):** Removes unneeded commits from the branch history.

---

## 🔒 Safety Rules

> [!CAUTION]
> **NEVER rebase a public or shared branch like `main`!**  
> Rebase recalculates SHA commit hashes. Rebasing a shared branch forces collaborators to resolve massive synchronization conflicts and rewrites published history.

### Always use `--force-with-lease`
When pushing a rebased branch to GitHub, use:
```bash
git push origin <feature-branch> --force-with-lease
```
Unlike plain `--force` which blindly overwrites everything, `--force-with-lease` verifies that no teammate pushed new commits to the remote branch while you were rebasing.

---

## 🛠️ Step-by-Step Hands-On Guide

```bash
# 1. Create a feature branch and make 3 small commits
git checkout -b feature/rebase-practice
echo "wip 1" >> test.txt && git commit -am "wip: start feature"
echo "wip 2" >> test.txt && git commit -am "fix: typo in feature"
echo "wip 3" >> test.txt && git commit -am "feat: finalize feature"

# 2. Start interactive rebase for last 3 commits
git rebase -i HEAD~3

# 3. In the editor that opens:
# Change:
#   pick abc1234 wip: start feature
#   pick def5678 fix: typo in feature
#   pick ghi9012 feat: finalize feature
# To:
#   pick abc1234 wip: start feature
#   squash def5678 fix: typo in feature
#   squash ghi9012 feat: finalize feature

# 4. Save and close. Git opens a second editor to write the unified commit message:
#   feat: complete rebase practice feature with all fixes

# 5. Push safely:
git push origin feature/rebase-practice --force-with-lease
```
