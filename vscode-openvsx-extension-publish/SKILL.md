---
name: vscode-openvsx-extension-publish
description: Workflow for publishing VSCode extensions to both VS Code Marketplace and Open VSX. Supports preparing package.json and README, creating accounts and tokens, local testing, initial manual publish, and setting up GitHub Actions for automated subsequent publishes. Use this skill when asked to "publish an extension", "publish to marketplace", "distribute a VSCode extension", "publish to Open VSX", or "set up CI/CD for an extension". Proactively use this when the extension implementation is mostly complete and the user wants to publish.
---

# VSCode & Open VSX Extension Publish

Workflow for publishing VSCode extensions to both VS Code Marketplace and Open VSX.

## Prerequisites

- Extension implementation is mostly complete
- Node.js is installed
- A GitHub repository exists

## Workflow Overview

1. **Account & Token Verification** — Check that required accounts and tokens are ready; guide creation if missing
2. **Pre-publish Preparation** — Prepare package.json, README, LICENSE, .vscodeignore, etc.
3. **Local Testing** — Verify the extension works correctly before publishing
4. **Initial Publish** — Publish to both VS Code Marketplace and Open VSX
5. **GitHub Actions Setup** — Create a workflow to automate subsequent publishes

---

## Phase 1: Account & Token Verification

Start by confirming the following with the user. Guide them through creation of anything that is missing.

### Checklist

Ask the user to determine their current status:

1. Do you have a **VS Code Marketplace Publisher**?
2. Do you have an **Azure DevOps Personal Access Token (PAT)**?
3. Do you have an **Open VSX (open-vsx.org) account**?
4. Do you have an **Open VSX Access Token**?

### 1-1: Creating a VS Code Marketplace Publisher

If the user does not have a Publisher:

1. Direct them to https://marketplace.visualstudio.com/manage
2. Sign in with a Microsoft account (create one if needed)
3. Click "Create Publisher" and configure:
   - **ID**: A unique identifier (cannot be changed later; all lowercase, hyphens allowed)
   - **Name**: The name displayed on the marketplace
4. Ask for the created Publisher ID

### 1-2: Creating an Azure DevOps PAT

If the user does not have a PAT:

1. Go to **https://aex.dev.azure.com** (using `dev.azure.com` may redirect to the Azure DevOps product page, so use this URL instead)
2. Sign in with a Microsoft account. If no organization exists, create one with any name
3. Once the organization is created, go directly to the PAT creation page: `https://dev.azure.com/<org-name>/_usersSettings/tokens`
4. Click "New Token" and configure:
   - **Name**: Any name (e.g., `vscode-marketplace`)
   - **Organization**: Select **"All accessible organizations"** (this is important — selecting a specific org may cause 403 errors)
   - **Expiration**: Any duration (up to 1 year)
   - **Scopes**: Select "Custom defined" → Click **"Show all scopes"** → Check **Marketplace** → **Manage**
5. Tell the user to copy and securely save the token (it is only displayed once)

### 1-3: Creating an Open VSX Account

If the user does not have an account:

1. Create an Eclipse account at https://accounts.eclipse.org
   - GitHub account linking is required, so verify the GitHub username is correct
2. Log in to https://open-vsx.org with GitHub
3. Authenticate with the Eclipse account from profile settings
4. Review and accept the **Publisher Agreement**

### 1-4: Creating an Open VSX Access Token

If the user does not have a token:

1. Go to https://open-vsx.org → Settings → Access Tokens
2. Click "Generate New Token" to create a token
3. Tell the user to copy and securely save the token (it is only displayed once)

### 1-5: Creating an Open VSX Namespace

Open VSX requires a "Namespace" corresponding to the Publisher ID. Create one with the same name as the user's Publisher ID:

```bash
npx ovsx create-namespace <publisher-id> -p <openvsx-token>
```

Skip this step if the namespace already exists.

---

## Phase 2: Pre-publish Preparation

### 2-1: Validating and Fixing package.json

Read the package.json and validate the following fields. Suggest fixes for any missing or incorrect values.

**Required fields:**

| Field            | Description                         | Example                      |
| ---------------- | ----------------------------------- | ---------------------------- |
| `name`           | Extension identifier                | `my-extension`               |
| `displayName`    | Name displayed on the marketplace   | `My Extension`               |
| `description`    | Brief description                   | `A helpful VSCode extension` |
| `version`        | SemVer format                       | `0.1.0`                      |
| `publisher`      | Publisher ID (confirmed in Phase 1) | `my-publisher`               |
| `engines.vscode` | Supported VSCode version            | `^1.80.0`                    |
| `categories`     | Categories (array)                  | `["Other"]`                  |

**Recommended fields:**

| Field        | Description                              | Example                                            |
| ------------ | ---------------------------------------- | -------------------------------------------------- |
| `icon`       | Icon image path (PNG, 128x128 or larger) | `icon.png`                                         |
| `repository` | GitHub repository URL                    | `{"type": "git", "url": "https://github.com/..."}` |
| `license`    | License                                  | `MIT`                                              |
| `keywords`   | Search keywords (up to 30)               | `["vscode", "tool"]`                               |
| `homepage`   | Homepage URL                             | Can be the same as the repository URL              |
| `bugs`       | Issue tracker URL                        | `{"url": "https://github.com/.../issues"}`         |

**About activationEvents:**

- Even without `activationEvents` in `package.json`, VSCode can automatically infer them from the `contributes` section, so explicit declaration is often unnecessary
- However, if `*` (activate on all events) is used, suggest narrowing it to specific events

**About engines.vscode:**

- Specify the minimum VSCode API version required by the extension
- If unknown, suggest a relatively recent version like `^1.80.0`

### 2-2: Preparing README.md

The README becomes the body of the extension page on the marketplace. Suggest the following structure:

```markdown
# Extension Name

Brief description (1-2 sentences)

## Features

- Description of feature 1
- Description of feature 2

(Screenshots or GIFs are recommended)

## Usage

How to use the extension

## Extension Settings

Describe settings if any

## Release Notes

### x.x.x

- Changes
```

If a README already exists, only suggest additions for missing sections. Do not over-rewrite.

### 2-3: LICENSE File

If no LICENSE file exists, suggest creating one. Ensure it matches the `license` field in package.json.

### 2-4: CHANGELOG.md

If no CHANGELOG exists, create a minimal one:

```markdown
# Changelog

## [0.1.0]

- Initial release
```

### 2-5: Preparing .vscodeignore

If `.vscodeignore` does not exist, create one. Exclude development files to keep the package size small:

```
.vscode/**
.vscode-test/**
.github/**
src/**
node_modules/**
.gitignore
.eslintrc*
tsconfig.json
*.ts
!*.d.ts
**/*.map
```

For TypeScript projects, exclude source files and only include compiled files.
Adjust according to the actual project structure.

### 2-6: Icon Generation

If package.json has `"icon": "icon.png"` but the file does not exist, or if the `icon` field is missing entirely, generate an icon.

1. Generate an SVG representing the extension's functionality (create a temporary file `_generate-icon.mjs`):

```js
// _generate-icon.mjs
import { writeFileSync } from "fs";
const size = 256;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e"/>
      <stop offset="100%" style="stop-color:#16213e"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="32" fill="url(#bg)"/>
  <!-- Design an icon here that represents the extension's functionality -->
</svg>`;
writeFileSync("icon.svg", svg);
```

2. Convert SVG to PNG:

```bash
node _generate-icon.mjs
npx sharp-cli -i icon.svg -o icon.png resize 256 256
```

3. Delete temporary files:

```bash
rm _generate-icon.mjs icon.svg
```

4. Add `"icon": "icon.png"` to package.json if not already present

**Note:** The icon must be a PNG file of at least 128x128 pixels. 256x256 is recommended. Adjust the SVG content to match the extension's functionality.

### 2-7: vscode:prepublish Script

For TypeScript projects, check that `package.json` has a `vscode:prepublish` script in `scripts`:

```json
{
	"scripts": {
		"vscode:prepublish": "npm run compile"
	}
}
```

Adjust the build command to match the project's actual setup (tsc, esbuild, webpack, etc.).

---

## Phase 3: Local Testing

Before publishing, verify that the extension works correctly. Fixing issues here prevents problems after publishing.

### 3-1: Testing with Extension Development Host

Guide the user through the following:

1. Open the project folder in VSCode
2. Press `F5` (or go to "Run and Debug" → "Run Extension") to launch the Extension Development Host
3. In the new VSCode window, verify the extension's functionality:
   - Do registered commands appear in the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)?
   - Does each feature work as expected?
   - Are there any errors in the Debug Console?

If `.vscode/launch.json` does not exist, create it:

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Run Extension",
			"type": "extensionHost",
			"request": "launch",
			"args": ["--extensionDevelopmentPath=${workspaceFolder}"]
		}
	]
}
```

### 3-2: Testing from .vsix File

Verify the extension works correctly when packaged:

```bash
npx @vscode/vsce package
```

Install the generated `.vsix` file in VSCode to verify:

```bash
code --install-extension <name>-<version>.vsix
```

After installation, guide the user to restart VSCode and verify the extension works correctly.
Once testing is complete, uninstall the test extension:

```bash
code --uninstall-extension <publisher>.<name>
```

---

## Phase 4: Initial Publish

### 4-1: Package Creation (Dry Run)

First, install `vsce` and create a package:

```bash
npx @vscode/vsce package
```

Check the output:

- Is the file size reasonable?
- Are any unnecessary files included?
- Are there any warnings or errors?

If there are issues, go back to Phase 2 and fix them.

### 4-2: Publish to VS Code Marketplace

Confirm with the user before publishing.

```bash
npx @vscode/vsce publish
```

The user will be prompted to enter the PAT — they should paste it in the terminal. Have the user run this command.

On success, share the marketplace URL:
`https://marketplace.visualstudio.com/items?itemName=<publisher>.<extension-name>`

**Note:** It may take a few minutes for the extension to appear.

### 4-3: Publish to Open VSX

Use the same `.vsix` file created for VS Code Marketplace:

```bash
npx ovsx publish <file>.vsix -p <openvsx-token>
```

Or publish directly from source:

```bash
npx ovsx publish -p <openvsx-token>
```

On success, share the Open VSX URL:
`https://open-vsx.org/extension/<namespace>/<extension-name>`

### 4-4: Post-publish Verification

Verify the extension appears on both marketplaces:

```bash
# VS Code Marketplace
npx @vscode/vsce show <publisher>.<extension-name>

# Open VSX (check in browser)
# https://open-vsx.org/extension/<namespace>/<extension-name>
```

### 4-5: Claiming Open VSX Namespace Ownership

After publishing to Open VSX, the extension page may display a "not a verified publisher" warning banner. To resolve this, you need to claim namespace ownership.

Create an issue in the `EclipseFdn/open-vsx.org` repository using the `gh` command:

```bash
gh issue create --repo EclipseFdn/open-vsx.org \
  --title "Claiming namespace <publisher-id>" \
  --label "namespace,operations" \
  --body "I am the owner of the GitHub account https://github.com/<github-username> and I would like to claim ownership of the \`<publisher-id>\` namespace on Open VSX. I have already logged in to https://open-vsx.org and published an extension (<extension-name>) under this namespace."
```

It may take several days for Eclipse Foundation staff to review and approve the request. Once approved, the warning banner will be removed and a verified badge will appear.

**Prerequisite:** The user must have logged in to https://open-vsx.org at least once.

---

## Phase 5: GitHub Actions Setup

### 5-1: Configuring Secrets

Guide the user to add secrets to the GitHub repository:

1. Go to repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - **`VSCE_PAT`**: Azure DevOps PAT (for VS Code Marketplace)
   - **`OVSX_PAT`**: Open VSX Access Token

### 5-2: Creating the Workflow File

Create `.github/workflows/publish.yml`:

```yaml
name: Publish Extension

on:
  push:
    tags:
      - "*"

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - run: npm ci

      - name: Publish to VS Code Marketplace
        run: npx @vscode/vsce publish -p ${{ secrets.VSCE_PAT }}

      - name: Publish to Open VSX
        run: npx ovsx publish -p ${{ secrets.OVSX_PAT }}
```

Adjust according to the project setup:

- **Package manager**: Change `npm ci` to match npm / yarn / pnpm
- **Build step**: If `vscode:prepublish` is defined, `vsce publish` runs it automatically, so a separate build step is usually unnecessary
- **Node.js version**: Match the project's requirements

### 5-3: Release Flow Explanation

Explain the release process to the user:

```bash
# 1. Update the version (automatically creates a commit and tag)
npm version patch  # or minor, major

# 2. Push with tags → GitHub Actions automatically publishes
git push --follow-tags
```

This triggers automatic publishing to both marketplaces whenever a tag is pushed.

---

## Troubleshooting

| Error                           | Cause                                                                                | Solution                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| `403 Forbidden` (vsce)          | PAT scope is incorrect, or Organization is not set to "All accessible organizations" | Recreate the PAT and verify the Org setting and Marketplace Manage scope |
| `Extension name already exists` | An extension with the same name already exists                                       | Change the `name` in package.json                                        |
| `Missing publisher`             | `publisher` is missing from package.json                                             | Add the `publisher` field                                                |
| Namespace mismatch (ovsx)       | The Open VSX Namespace does not exist or does not match the publisher                | Create it with `npx ovsx create-namespace`                               |
| Icon-related errors             | Icon is smaller than 128x128 or is not a PNG                                         | Provide a PNG file of at least 128x128                                   |
