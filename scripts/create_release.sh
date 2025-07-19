#!/usr/bin/env bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PUSH=false
VERSION=""
DRY_RUN=false

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] VERSION

Create a new release for Algo Quantum VPN

OPTIONS:
    --push          Push the tag to remote repository
    --dry-run      Show what would be done without executing
    -h, --help     Show this help message

EXAMPLES:
    $0 1.0.0                    # Create local tag v1.0.0
    $0 --push 1.0.0            # Create and push tag v1.0.0
    $0 --dry-run --push 1.0.0  # Show what would happen

EOF
}

# Function to log messages
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option $1"
            ;;
        *)
            if [ -z "$VERSION" ]; then
                VERSION="$1"
            else
                error "Multiple versions specified"
            fi
            shift
            ;;
    esac
done

# Validate version is provided
if [ -z "$VERSION" ]; then
    error "Version is required"
fi

# Validate version format (basic semver check)
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$'; then
    error "Version must follow semantic versioning (e.g., 1.0.0 or 1.0.0-beta.1)"
fi

# Add v prefix to version for git tag
TAG_VERSION="v$VERSION"

log "Creating release for version: $TAG_VERSION"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    error "Not in a git repository"
fi

# Check if working directory is clean
if [ "$DRY_RUN" = false ] && [ -n "$(git status --porcelain)" ]; then
    warn "Working directory is not clean. Uncommitted changes:"
    git status --short
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Aborted due to uncommitted changes"
    fi
fi

# Check if tag already exists
if git tag | grep -q "^$TAG_VERSION$"; then
    error "Tag $TAG_VERSION already exists"
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log "Current branch: $CURRENT_BRANCH"

# Create release directory
RELEASE_DIR="releases"
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$RELEASE_DIR"
fi

# Create archive name
ARCHIVE_BASE="algo-quantum-$TAG_VERSION"

# Function to create archives
create_archives() {
    log "Creating release archives..."

    if [ "$DRY_RUN" = false ]; then
        # Create tar.gz archive
        git archive --format=tar.gz --prefix="$ARCHIVE_BASE/" HEAD > "$RELEASE_DIR/$ARCHIVE_BASE.tar.gz"
        log "Created $RELEASE_DIR/$ARCHIVE_BASE.tar.gz"

        # Create zip archive
        git archive --format=zip --prefix="$ARCHIVE_BASE/" HEAD > "$RELEASE_DIR/$ARCHIVE_BASE.zip"
        log "Created $RELEASE_DIR/$ARCHIVE_BASE.zip"
    else
        log "Would create $RELEASE_DIR/$ARCHIVE_BASE.tar.gz"
        log "Would create $RELEASE_DIR/$ARCHIVE_BASE.zip"
    fi
}

# Function to create git tag
create_tag() {
    log "Creating git tag: $TAG_VERSION"

    if [ "$DRY_RUN" = false ]; then
        git tag -a "$TAG_VERSION" -m "Release $TAG_VERSION

Automated release created by create_release.sh script.

Release includes quantum-safe VPN enhancements and Algo VPN improvements."
        log "Created git tag: $TAG_VERSION"
    else
        log "Would create git tag: $TAG_VERSION"
    fi
}

# Function to push tag
push_tag() {
    if [ "$PUSH" = true ]; then
        log "Pushing tag to remote repository..."

        if [ "$DRY_RUN" = false ]; then
            git push origin "$TAG_VERSION"
            log "Pushed tag $TAG_VERSION to origin"
        else
            log "Would push tag $TAG_VERSION to origin"
        fi
    fi
}

# Function to update CHANGELOG
update_changelog() {
    if [ -f "CHANGELOG.md" ]; then
        log "CHANGELOG.md found - consider updating it manually"
    else
        warn "No CHANGELOG.md found - consider creating one"
    fi
}

# Main execution
main() {
    if [ "$DRY_RUN" = true ]; then
        warn "DRY RUN MODE - No changes will be made"
    fi

    log "Starting release process for $TAG_VERSION"

    create_archives
    create_tag
    push_tag
    update_changelog

    if [ "$DRY_RUN" = false ]; then
        log "Release $TAG_VERSION created successfully!"
        log "Archive files created in $RELEASE_DIR/"

        if [ "$PUSH" = true ]; then
            log "Tag pushed to remote repository"
            log "GitHub Actions should now create the GitHub release"
        else
            log "To push the tag, run: git push origin $TAG_VERSION"
        fi
    else
        log "Dry run completed - no changes were made"
    fi
}

# Run main function
main
