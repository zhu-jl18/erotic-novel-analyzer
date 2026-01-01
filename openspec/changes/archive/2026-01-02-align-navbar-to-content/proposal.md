# Change: Align navbar content to main content area

## Why
The navbar title ("小说分析器") and icons are positioned at the screen edges (px-6), while the main content uses `max-w-4xl mx-auto px-6`. This creates visual misalignment - the header elements don't line up with the content below.

## What Changes
- Wrap navbar inner content with `max-w-4xl mx-auto px-6 w-full` container
- Remove padding from outer navbar div (keep only sticky/backdrop styles)
- Inner content alignment matches main content area

## Impact
- Affected files: `templates/index.html`
- Visual only - no functional changes
- No breaking changes
