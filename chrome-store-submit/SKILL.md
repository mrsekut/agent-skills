---
name: chrome-store-submit
description: Automate new Chrome extension submission to Chrome Web Store using playwright-mcp. Reads manifest.json and source code, generates store listing text in any language, creates store images, and fills all required forms via browser automation. Use when submitting a new Chrome extension to Chrome Web Store, publishing a Chrome extension, or filling Chrome Web Store developer dashboard forms.
---

# Chrome Web Store Submission

Automate the Chrome Web Store new extension submission process using playwright-mcp browser automation.

## Prerequisites

- playwright-mcp configured as MCP server. See [references/setup.md](references/setup.md) if not set up.
- Pillow installed (`pip install Pillow`) for image generation.
- Extension source code with valid `manifest.json` in the working directory.
- Extension packaged as ZIP file ready for upload.

## Workflow

1. **Gather extension info** from source code
2. **Launch browser** → ユーザがログイン → ZIPアップロード
3. **Scan all tabs** to identify required fields and current state
4. **Ask user** for source code から判断できない項目だけ質問
5. **Generate store images and listing text**
6. **Fill all forms** across all tabs
7. **Save as draft** and prompt user to review

## Step 1: Gather Extension Info

Read these files from the project to extract info:

```
manifest.json → name, short_name, description, permissions, version, icons
README.md → feature descriptions, usage details (if exists)
```

Extract:

- `name` (max 75 chars for store)
- `description` (used as short description, max 132 chars)
- `permissions` (needed for privacy justification)
- `version`
- `icons` (path to largest icon for image generation)

## Step 2: Browser Launch and Upload

1. Navigate to `https://chrome.google.com/webstore/devconsole`
2. Tell the user: "Please log in to your Google Developer account in the browser. Let me know when you're done."
3. Wait for user confirmation.
4. Click "New item" or equivalent upload button.
5. Use `browser_file_upload` to upload the ZIP file.
6. Wait for upload to complete and dashboard to load.

## Step 3: Scan All Tabs

Upload 後のダッシュボードで全タブを巡回し、必須項目を洗い出す。

1. **Store Listing tab**: `browser_snapshot` で必須フィールドと現在の状態を確認
2. **Privacy Practices tab**: サイドバーから遷移 → `browser_snapshot`
3. **Distribution tab**: サイドバーから遷移 → `browser_snapshot`

各タブで以下を記録する:
- 必須フィールド名と入力タイプ（テキスト、ドロップダウン、ファイルアップロード、チェックボックスなど）
- すでに値が入っているフィールド（manifest.json から自動入力されるものがある）
- 空欄の必須フィールド

## Step 4: Ask User for Missing Info

Step 1 のソースコード情報と Step 3 のフォーム状態を突き合わせ、**自動で埋められない必須項目だけ**をユーザに質問する。

ソースコードから判断できる可能性が高いもの（質問しない）:
- Extension name, description（manifest.json）
- Permission justifications（permissions + ソースコードの用途から推測）
- Remote code declaration（MV3 なら通常 No）
- Data collection の有無（permissions とソースコードから推測）

ユーザへの質問が必要になりやすいもの:
- **Target language** for store listing
- **Primary category**
- **Privacy policy URL**
- **Brand color** (hex, for image generation)
- **Visibility** (Public / Unlisted / Private)

ただし上記はあくまで傾向であり、実際のフォーム状態に基づいて判断すること。不要な質問はしない。

## Step 5: Generate Store Images and Listing Text

### Images

```bash
python3 scripts/generate_store_images.py <icon_path> <output_dir> --name "Extension Name" --color "#hexcolor"
```

This generates:

- `store_icon_128.png` (128x128, with 16px transparent padding)
- `promo_tile_440x280.png` (440x280, small promo tile)
- `marquee_1400x560.png` (1400x560, marquee tile)
- `screenshot_1280x800.png` (1280x800, placeholder screenshot)

Ask the user if they want to use these generated images or provide their own.

### Listing Text

Based on manifest.json info and README, generate in the user's target language:

- **Detailed description**: 2-4 paragraphs covering what the extension does, key features, and how to use it. No HTML, plain text only.
- **Single purpose description**: 1-2 sentences clearly stating the extension's primary functionality.
- **Permission justifications**: One sentence per permission explaining why it's needed.

Show all generated text to the user for approval before filling forms.

## Step 6: Fill All Forms

各タブに戻り、フォームを入力する。各フィールド操作の前に `browser_snapshot` で現在の状態を確認すること。

### Store Listing Tab

1. Fill **Detailed Description** textarea
2. Select **Primary Category** from dropdown
3. Select **Language** from dropdown
4. Upload **Store Icon** (128x128)
5. Upload **Screenshots** (1280x800)
6. Upload **Small Promo Tile** (440x280)
7. Optionally upload **Marquee Promo Tile**

### Privacy Practices Tab

1. Fill **Single Purpose Description**
2. Fill **Permission Justifications** (one per permission from manifest)
3. Set **Remote Code Declaration**
4. Handle **Data Usage Disclosures** and **Limited Use Certification**
5. Enter **Privacy Policy URL**

### Distribution Tab

1. Set **Visibility** (Public/Unlisted/Private)
2. Set **Geographic Distribution** (default: All regions)

## Step 7: Save as Draft

1. Click "Save Draft" button (NOT "Submit for Review")
2. Verify save succeeded via `browser_snapshot`
3. Tell user: "Draft saved successfully. Please review all fields in the browser before submitting for review."

## Important Notes

- Always use `browser_snapshot` before interacting with page elements to find correct selectors.
- Chrome Web Store dashboard is a SPA; wait after navigation for content to load.
- If a form field is not found, take a screenshot and ask the user for guidance.
- Never click "Submit for Review" — only save as draft.
- For form field details and constraints, see [references/store-fields.md](references/store-fields.md).
