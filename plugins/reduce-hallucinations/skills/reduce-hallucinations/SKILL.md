---
name: reduce-hallucinations
description: Use for investigation, research, fact-finding, or document/report analysis tasks (e.g. "look into this", "analyze this report", "fact-check this") where claims must be grounded in verifiable evidence. Grounds answers in direct quotes and citations, and permits acknowledging uncertainty instead of guessing. Do NOT use for implementation, coding, refactoring, or bug-fixing tasks — citations and source references do not belong in code or code comments.
---

# Reduce Hallucinations

Source: [Claude Docs - Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)

Minimize hallucinations by permitting uncertainty, grounding answers in direct quotes, and verifying claims against citations.

## Basic strategies

- **Allow "I don't know"**: when information is insufficient or confidence is low, say so explicitly instead of filling the gap with a guess.
- **Ground facts in direct quotes**: for long documents (roughly 20k+ tokens), first extract verbatim quotes of the relevant passages, then base the answer on those quotes.
- **Verify claims with citations**: back each claim in the answer with a citation or source. Retract or flag any claim that has no supporting citation.

## Advanced techniques

- **Chain-of-thought verification**: walk through the reasoning step by step before giving a final answer, to surface faulty premises or logical leaps.
- **Best-of-N verification**: run the same prompt multiple times and compare the outputs — inconsistencies across runs can indicate hallucination.
- **Iterative refinement**: feed a prior answer back in as input for a follow-up pass that re-verifies or extends it, catching and fixing inconsistencies.
- **Restrict external knowledge**: prefer the provided documents/codebase over general knowledge, and say so explicitly when something can't be determined from them alone.

## How to apply

- Cite grounding evidence in the answer — file paths, line numbers, source URLs.
- For fact-checking, read the actual code or document rather than guessing.
- These techniques reduce hallucinations significantly but don't eliminate them — always verify information behind high-stakes decisions.
- Do not apply this skill to implementation/coding tasks. Source citations do not belong in code comments.
