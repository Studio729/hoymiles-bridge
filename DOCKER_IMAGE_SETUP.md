# Docker Image Automated Build Setup

This project is configured to automatically build and publish Docker images to GitHub Container Registry (GHCR) when code is pushed to GitHub.

## How It Works

### GitHub Actions Workflow

The `.github/workflows/docker.yml` workflow automatically:

1. **Triggers on**:
   - Push to `main` or `master` branch → builds `latest` tag
   - Push of version tags (e.g., `v1.0.0`) → builds versioned tags
   - Pull requests → builds test images (not pushed)

2. **Builds multi-platform images**:
   - `linux/amd64` (x86_64)
   - `linux/arm64` (ARM64/aarch64)

3. **Tags created**:
   - `latest` - Latest build from main/master branch
   - `v1.0.0` - Exact version tag
   - `v1.0` - Minor version tag
   - `v1` - Major version tag

### Published Image Location

Images are published to:
```
ghcr.io/studio729/hoymiles-bridge:latest
ghcr.io/studio729/hoymiles-bridge:v1.0.0
```

## Usage

### In Docker Compose (Portainer Stack)

Your `docker-compose.yml` is configured to use the pre-built image:

```yaml
hoymiles-smiles:
  image: ghcr.io/studio729/hoymiles-bridge:latest
```

### Pull the Image

```bash
docker pull ghcr.io/studio729/hoymiles-bridge:latest
```

### Use in Portainer

Simply copy your `docker-compose.yml` into a Portainer stack and deploy. Portainer will automatically pull the pre-built image from GHCR.

## Making the Repository Public Images Available

By default, GitHub Container Registry packages are private. To make them public:

1. Go to your GitHub repository
2. Navigate to Packages (right side of repo page)
3. Click on the `hoymiles-bridge` package
4. Go to **Package settings**
5. Scroll to **Danger Zone**
6. Click **Change visibility** → **Public**

Alternatively, keep them private and authenticate Docker:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

## Triggering a Build

### Automatic Build (Push to Main)
```bash
git add .
git commit -m "Update code"
git push origin main
```

### Tagged Release
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### Manual Trigger
Go to GitHub → Actions → "Build and Push Docker Image" → Run workflow

## Using Specific Versions

To use a specific version in your docker-compose.yml:

```yaml
hoymiles-smiles:
  image: ghcr.io/studio729/hoymiles-bridge:v1.0.0  # Specific version
  # or
  image: ghcr.io/studio729/hoymiles-bridge:latest  # Latest main branch
  # or
  image: ghcr.io/studio729/hoymiles-bridge:main    # Main branch (updated on every push)
```

## Build Cache

The workflow uses GitHub Actions cache to speed up builds. Subsequent builds will be much faster.

## Monitoring Builds

Check build status:
- GitHub → Actions tab
- Look for "Build and Push Docker Image" workflow runs
- Green checkmark = successful build
- Red X = failed build (check logs)

## Local Development

If you want to build locally instead:

```bash
docker build -t hoymiles-bridge:local .
```

Then use `hoymiles-bridge:local` in your docker-compose.yml for testing.

