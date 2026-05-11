# Installation Guide

## Prerequisites

- Python 3.12+
- [Claude Code](https://claude.ai/code) CLI installed
- [`gws`](https://github.com/nicholasgasior/gws) CLI for Google Workspace API access
- Google Cloud project with the Slides API and Drive API enabled
- OAuth credentials configured for `gws`

### Optional

- `matplotlib >= 3.8` -- required only for LaTeX formula rendering

## Step 1 -- Install the Python package

```bash
cd google-slides-skill
pip install -e .
```

To include formula support:

```bash
pip install -e ".[formulas]"
```

## Step 2 -- Configure Google API credentials

The skill uses `gws` to interact with Google Slides and Drive APIs. Set up `gws` with your Google Cloud credentials:

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable the **Google Slides API** and **Google Drive API**
3. Create OAuth 2.0 credentials (Desktop application type)
4. Run `gws auth login` to authenticate

Verify the setup:

```bash
gws slides presentations create --title "Test" --json
```

This should return a JSON response with a `presentationId`. Delete the test presentation afterward.

## Step 3 -- Register the skill with Claude Code

Copy `skill.md` to your Claude Code commands directory:

```bash
# For project-level registration (recommended)
mkdir -p .claude/commands
cp google-slides-skill/skill.md .claude/commands/google-slides.md

# Or for user-level registration (available in all projects)
mkdir -p ~/.claude/commands
cp google-slides-skill/skill.md ~/.claude/commands/google-slides.md
```

The skill will be available as `/google-slides` in Claude Code.

## Step 4 -- Verify the installation

1. Open Claude Code in a project where the skill is registered
2. Type `/google-slides` -- the skill should appear in the command list
3. Ask it to create a simple test presentation:
   ```
   /google-slides Create a 3-slide presentation about Python best practices
   ```

## Customization

### Changing the skill name

Rename the file in `.claude/commands/` to change the slash command. For example, `slides.md` makes it available as `/slides`.

### Updating the skill path

If the `google_slides_skill` package is installed in a non-standard location, ensure it is importable from the environment where Claude Code runs:

```bash
python -c "from google_slides_skill import get_layout; print('OK')"
```

### Sharing presentations

To auto-share created presentations, add sharing instructions to the skill prompt or pass `--share` flags to `gws` commands in your build scripts.
