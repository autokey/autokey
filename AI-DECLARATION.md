# AI Declaration Policy

## Overview

This project requires transparency regarding AI usage in contributions. All pull requests that involve AI assistance must include a declaration as outlined below.

This policy aims to:
- Maintain transparency about AI involvement in contributions
- Ensure proper scrutiny of AI-generated content
- Prevent AI "slop" submissions that don't meet quality standards
- Build trust with the community

## Required Declaration

For any pull request that involves AI-generated content, contributors must:

1. **Complete the AI Declaration section** in the pull request template
2. **Select the appropriate AI usage level** (see below)
3. **Provide context** on how AI was used in the contribution

## AI Usage Levels

Choose the level that best describes your contribution:

| Level | Description |
|-------|-------------|
| **none** | No AI was used; the work is entirely human-generated |
| **hint** | AI was used only to surface suggestions (e.g., IDE autocomplete); human makes all decisions |
| **assist** | AI assisted with part of the task (e.g., drafting tests, documentation); human prompted and reviewed |
| **pair** | Human and AI worked together equally; human understands all internals |
| **copilot** | AI completed most of the task at human's direction; human reviewed and approved |
| **auto** | AI completed the task autonomously with minimal human guidance |

## Examples

### Example 1: AI Assist Level

```
AI Usage Level: assist

AI was used to draft initial documentation for the new API endpoints.
I reviewed all AI-generated content, made modifications, and verified accuracy.
```

### Example 2: AI Copilot Level

```
AI Usage Level: copilot

AI generated the initial implementation of the data parsing module based on my detailed
specification. I reviewed every function, ran tests, and made significant modifications
to ensure it met project standards.
```

## Requirements for AI-Assisted Contributions

All AI-assisted contributions must:

- **Disclose AI usage** at the top of the PR description
- **Describe what AI was used for** and what the human's role was
- **Include thorough human review** of all AI-generated content
- **Meet the same quality standards** as fully human-generated contributions
- **Be accompanied by tests** that verify the functionality

## Rejection Criteria

Pull requests may be rejected if they:
- Fail to declare AI usage when AI was involved
- Contain AI-generated content that appears unreviewed
- Are deemed to be "AI slop" (low-quality AI output without proper human oversight)
- Come from accounts that appear to be dummy/fake

## Why This Policy Exists

AI-assisted coding is a reality of our time. We recognize that AI tools can be incredibly helpful, but we also see many low-quality AI-generated submissions that waste reviewers' time and can introduce vulnerabilities or technical debt.

This policy helps us:
1. Apply appropriate scrutiny to AI-assisted contributions
2. Distinguish between thoughtful AI-assisted work and "AI slop"
3. Maintain the quality and security of our codebase
4. Be transparent with our community about our standards

## Questions

If you have questions about this policy or whether your contribution requires a declaration, please open an issue for discussion before submitting your PR.

## References

- [DimwitLabs AI-DECLARATION.md](https://github.com/DimwitLabs/AI-DECLARATION.md) - The standard this policy is based on
- [GitHub Discussion #1121](https://github.com/autokey/autokey/discussions/1121) - Original discussion

---

*Last updated: 2026-05-12*
