# Document Templates

## 1-context

```markdown
# Context: {Task Name}

## Tech Stack

- Framework:
- Language:
- Key libraries:

## Relevant Existing Code

- `path/to/file.ts`: Description of relevance
- `path/to/component/`: Description of relevance

## Project Conventions

- Naming:
- Directory structure:
- Patterns used:

## Constraints

-
```

## 2-prototyping-learnings

```markdown
# Prototyping Learnings: {Task Name}

## What Worked Well

-

## What Felt Awkward

-

## Discovered Requirements

Requirements or constraints that became apparent through prototyping:

-

## UX Insights

Insights that should influence the design:

-

## Notes

Additional observations:

-
```

## 3-requirements

```markdown
# Requirements: {Task Name}

## User Story

As a [user type], I want to [action] so that [benefit].

## Acceptance Criteria

- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Scope

### In Scope

- Item 1
- Item 2

### Out of Scope

- Item 1
- Item 2
```

## 4-design

````markdown
# Design: {Task Name}

## Domain Models

Core type definitions only. Not utility types or internal details.

```typescript
interface Article {
	id: ArticleId;
	title: string;
	content: Content;
	author: UserId;
}
```

## Feature Boundaries

| Feature | Responsibility          | Depends On    |
| ------- | ----------------------- | ------------- |
| article | Article CRUD operations | user, storage |
| user    | User management         | -             |
| storage | Persistence layer       | -             |

## Directory Structure (Package by Feature)

Feature-level structure only. Not detailed file structure within each feature.

```
src/
├── features/
│   ├── article/
│   ├── user/
│   └── storage/
└── shared/
    └── utils/
```

## Main Flow

Main processing steps with data transformation.

1. `validateInput`: RawInput → ValidatedInput
2. `fetchArticle`: ArticleId → Article
3. `transformForDisplay`: Article → ArticleViewModel
4. `render`: ArticleViewModel → ReactElement

## Layer Structure

Where each logic belongs. Push to core (innermost layer) as much as possible.

Identify project's layer hierarchy first, then assign each logic.

Example layers (React):

```
Core → State → Hooks → Components
```

Example layers (Backend):

```
Domain → Application → Controller → Handler
```

| Logic         | Layer         | Reason                         |
| ------------- | ------------- | ------------------------------ |
| validateInput | Core          | Pure function, no dependencies |
| fetchArticle  | Core          | Can be injected, testable      |
| ...           | (outer layer) | Needs framework/infra          |
````

## 5-implementation-plan

```markdown
# Implementation Plan {N}: {PR Title}

## Overview

Brief description of what this PR accomplishes.

## Dependencies

- Requires: 5-implementation-plan-{X} (if any)
- Blocks: 5-implementation-plan-{Y} (if any)
- Parallel: Can run alongside 5-implementation-plan-{Z}

## Tasks

### Setup

- [ ] Task 1
- [ ] Task 2

### Core Implementation

- [ ] Task 3
- [ ] Task 4

### Reviewability

How this PR can be reviewed:

- [ ] Tests demonstrate expected behavior
- [ ] (or) Types define clear interfaces
- [ ] (or) Working UI allows manual verification

### Verification

- [ ] tsc passes
- [ ] lint passes
- [ ] tests pass

## Suggested Commits

1. `feat: add base structure for feature`
2. `feat: implement core logic`
3. `test: add tests for feature`
```
