# Chrome Web Store Submission Form Fields Reference

## Tab: Store Listing

### Product Details

| Field                       | Type                                    | Required | Constraints                                                         |
| --------------------------- | --------------------------------------- | -------- | ------------------------------------------------------------------- |
| Extension Name              | Text (from manifest.json `name`)        | Yes      | Max 75 chars                                                        |
| Summary / Short Description | Text (from manifest.json `description`) | Yes      | Max 132 chars, plain text                                           |
| Detailed Description        | Textarea                                | Yes      | Plain text, no HTML. Start with concise overview, then feature list |
| Primary Category            | Dropdown                                | Yes      | Single selection from 17 categories (see below)                     |
| Language                    | Dropdown                                | Yes      | Default language of extension                                       |

**Categories (17 total, 3 groups):**

_Productivity:_ Developer Tools, Education, Tools, Workflow & Planning
_Lifestyle:_ Art & Design, Entertainment, Games, Household, Just for Fun, News & Weather, Shopping, Social Networking, Travel, Well-being
_Make Chrome Yours:_ Accessibility, Functionality & UI, Privacy & Security

### Graphic Assets

| Field              | Type                   | Required | Constraints                                                      |
| ------------------ | ---------------------- | -------- | ---------------------------------------------------------------- |
| Store Icon         | File upload (PNG)      | Yes      | 128x128 px (96x96 artwork + 16px transparent padding)            |
| Screenshots        | File upload (PNG/JPEG) | Yes      | Min 1, max 5. 1280x800 or 640x400 px. Full bleed, square corners |
| Small Promo Tile   | File upload (PNG/JPEG) | Yes      | 440x280 px                                                       |
| Marquee Promo Tile | File upload (PNG/JPEG) | No       | 1400x560 px                                                      |
| YouTube Video Link | URL                    | No       | Promotional video                                                |

### Additional Fields

| Field          | Type     | Required | Constraints                        |
| -------------- | -------- | -------- | ---------------------------------- |
| Official URL   | Dropdown | No       | Verified via Google Search Console |
| Homepage URL   | URL      | No       | Extension info page                |
| Support URL    | URL      | No       | Dedicated support site             |
| Mature Content | Checkbox | No       | Restricts visibility if checked    |

## Tab: Privacy Practices

### Single Purpose

| Field                      | Type     | Required | Constraints                               |
| -------------------------- | -------- | -------- | ----------------------------------------- |
| Single Purpose Description | Textarea | Yes      | Clearly communicate primary functionality |

### Permissions Justification

One text field per permission declared in manifest.json. Must explain why each permission is needed.

### Remote Code

| Field                     | Type           | Required | Constraints                       |
| ------------------------- | -------------- | -------- | --------------------------------- |
| Remote Code Declaration   | Radio (Yes/No) | Yes      | MV3 cannot execute remote code    |
| Remote Code Justification | Textarea       | If Yes   | Explain why remote code is needed |

### Data Usage Disclosures

**Data collection checkboxes (check all that apply):**

- Personally identifiable information (name, address, phone, email, etc.)
- Health information
- Financial and payment information
- Authentication information (logins, passwords, cookies)
- Personal communications (emails, texts, chats)
- Location
- Web history (domains/URLs)
- User activity (clicks, mouse, scroll, keystrokes)
- Website content (text, images, sounds, videos)

**Limited Use Certification (must certify all 4):**

1. Data used only for single purpose or user-facing features
2. Data transfers only for necessity, legal, security, or mergers
3. Data not used for personalized/retargeted/interest-based ads
4. Humans do not read user data (except with consent, security, legal, aggregated)

### Privacy Policy

| Field              | Type | Required | Constraints                                  |
| ------------------ | ---- | -------- | -------------------------------------------- |
| Privacy Policy URL | URL  | Yes      | Must comprehensively disclose data practices |

## Tab: Distribution

| Field                   | Type         | Required   | Constraints                              |
| ----------------------- | ------------ | ---------- | ---------------------------------------- |
| In-App Purchases        | Checkbox     | No         | Check if using third-party paid features |
| Visibility              | Radio        | Yes        | Public / Unlisted / Private              |
| Trusted Testers         | Text         | If Private | Emails with Google accounts              |
| Geographic Distribution | Multi-select | Yes        | Default: All regions                     |

## Image Design Guidelines

- Avoid text in images (or keep minimal)
- Design should work at half-size
- Assume light gray background
- Use saturated colors
- Fill entire region
- Ensure well-defined edges
