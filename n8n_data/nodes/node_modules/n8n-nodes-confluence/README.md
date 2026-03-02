# n8n-nodes-Confluence

This is an n8n community node for Atlassian Confluence. It lets you query Confluence spaces and pages and, optionally, process images in page content with AI to replace image tags with its descriptions before extracting plaintext.

[n8n](https://n8n.io/) is a [fair-code licensed](https://docs.n8n.io/reference/license/) workflow automation platform.

[Installation](#installation)  
[Operations](#operations)  
[Credentials](#credentials)  
[Compatibility](#compatibility)  
[Usage](#usage)  
[Resources](#resources)  
[Version history](#version-history)

## Installation

Follow the [installation guide](https://docs.n8n.io/integrations/community-nodes/installation/) in the n8n community nodes documentation. After publishing/installation, restart n8n so it picks up the node from your installed package.

## Operations

The Confluence node under `Confluence` → `Space` supports:

- **Get Spaces** (`resource: space`, `operation: getSpaces`)
  - Lists spaces with pagination.
  - Parameters: Base URL, optional limit (internally paginated at 100 items).

- **Get Space Content** (`resource: space`, `operation: getSpaceContent`)
  - Fetches pages for a given space (storage format HTML included), processes images (optional), and returns both original HTML and extracted plaintext.
  - Parameters: Base URL, Space Key, Space Name (optional UI helper), Process Images (boolean), AI Provider/Model/Custom URL (when processing images).

## Credentials

The node uses one credential type:

- **Confluence Credentials API** (`confluenceCredentialsApi`)
  - Fields:
    - APIM Subscription Key (string, masked)
    - User Name (string)
    - Password / Token (string, masked)
  - Used for all Confluence REST API calls (e.g. `/rest/api/space/...`).

Image processing credentials: The AI API key is currently provided as a node parameter (password field) shown only when “Process Images” is enabled. This avoids a UI limitation with conditional display of credentials and ensures a clean configuration experience.

## Compatibility

- **Node.js**: >= 20 (see `engines` in `package.json`).
- **n8n**: Tested with n8n 1.106.x.
- The node compiles to `dist/` and registers via the `n8n` section in `package.json`:
  - Credentials: `dist/credentials/ConfluenceCredentialsApi.credentials.js`
  - Nodes: `dist/nodes/Confluence/Confluence.node.js`

## Usage

Basic steps:

- **Add node**: Search for “Confluence”.
- **Configure**: Set `Base URL` to your Confluence base (e.g. `https://your-domain.atlassian.net/wiki`).
- **Credentials**: Select “Confluence Credentials account” and provide the required fields.
- **Choose operation**:
  - Get Spaces to list available spaces.
  - Get Space Content to extract pages of a space.
- **Optional: Process Images**
  - Enable “Process Images” to analyze image attachments with an AI vision model and replace `<ac:image>`/`<img>` tags with short descriptions before HTML→text extraction.
  - Provide an API Key (password field).

Output for `Get Space Content` includes:

- **pages[]** each with: `spaceKey`, `spaceName`, `id`, `title`, `body` (original HTML), `plainText` (processed text), `webuiLink`.

Notes:

- Attachments are resolved via Confluence’s child attachment endpoint; image binaries are downloaded with proper `encoding: null` handling to preserve integrity for AI models.
- Pagination is handled internally with a page size of 100 and safe termination conditions.

### Local development

n8n doesn’t hot‑reload community nodes. To test locally:

1. Build the node

   ```bash
   npm run build
   ```

2. Link into n8n’s custom folder (one‑time)

   ```bash
   npm link // execute in the root of the repository
   mkdir -p ~/.n8n/custom
   cd ~/.n8n/custom
   npm link n8n-nodes-confluence
   ```

3. Start n8n locally (with debug logs enabled)

   ```bash
   N8N_LOG_LEVEL=debug N8N_LOG_PRETTY=true N8N_RUNNERS_ENABLED=true npx -y n8n
   ```

4. Develop
   - After code changes, run `npm run build` again.
   - Restart n8n to load the new build.

Notes

- If you change `package.json` entries (like the `n8n` registration), rebuild and restart n8n.
- If you use Docker, you can bind‑mount this package into `/home/node/.n8n/custom/node_modules/n8n-nodes-confluence/` and restart the container after builds.

## Publishing

Follow these steps to publish the package to npm:

1. Login to npm

   ```bash
   npm login
   ```

2. Verify metadata in `package.json`
   - `name`, `version`, `description`, `keywords` (include `n8n-community-node-package`), `repository`, `license`.
   - `files` includes `dist`, `README.md`, `LICENSE`.
   - `n8n` section correctly references built files in `dist/`.

3. Build and lint

   ```bash
   npm run prepublishOnly
   ```

4. Bump the version

   ```bash
   npm version patch   # or minor / major
   ```

5. Publish publicly

   ```bash
   npm publish --access public
   ```

6. Verify installation
   - Install into a clean environment or link into `~/.n8n/custom/`.
   - Restart n8n and confirm the node appears and works.

7. Release housekeeping (optional)
   - Tag the release in Git and create a GitHub release/changelog.

## Resources

- [n8n community nodes documentation](https://docs.n8n.io/integrations/#community-nodes)
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/)

## Version history

- **0.1.0**
  - Initial release: list spaces, fetch space content with storage HTML, optional AI image description replacement and plaintext extraction, robust attachment handling, and better error logging.
