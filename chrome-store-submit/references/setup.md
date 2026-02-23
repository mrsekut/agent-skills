# playwright-mcp Setup

## Prerequisites

- Node.js (or Bun) installed
- Chromium-based browser available

## Install playwright-mcp

Add to the project's `.mcp.json` (in the extension's repository root):

```json
{
	"mcpServers": {
		"playwright": {
			"command": "npx",
			"args": ["@playwright/mcp@latest"]
		}
	}
}
```

Or with Bun:

```json
{
	"mcpServers": {
		"playwright": {
			"command": "bunx",
			"args": ["@playwright/mcp@latest"]
		}
	}
}
```

### Options

- `--headless`: Run browser without visible window (default: headed)
- `--browser <name>`: Browser to use: chromium, firefox, webkit (default: chromium)
- `--port <number>`: Port for SSE transport
- `--user-data-dir <path>`: Custom browser profile directory (useful for persistent login sessions)
- `--viewport-width <px>` / `--viewport-height <px>`: Browser viewport size

### Recommended for Chrome Web Store

Use headed mode (no `--headless` flag) so the user can see the browser and manually log in.

To persist login across sessions:

```json
{
	"mcpServers": {
		"playwright": {
			"command": "npx",
			"args": [
				"@playwright/mcp@latest",
				"--user-data-dir",
				"/tmp/chrome-store-profile"
			]
		}
	}
}
```

## Available MCP Tools

Key tools from playwright-mcp used by this skill:

- `browser_navigate` - Navigate to URL
- `browser_click` - Click element (by text, CSS selector, coordinates)
- `browser_type` - Type into input field
- `browser_select_option` - Select dropdown option
- `browser_snapshot` - Get page accessibility snapshot (for finding elements)
- `browser_take_screenshot` - Take screenshot of current page
- `browser_file_upload` - Upload file to input
- `browser_tab_list` / `browser_tab_select` - Manage tabs
- `browser_wait` - Wait for specified time

## Verification

After configuring, restart Claude Code and verify by checking that playwright MCP tools appear in the tool list.
