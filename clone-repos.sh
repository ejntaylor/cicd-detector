#!/bin/bash

# Git Repository Cloning Script
# Clones repositories listed in repos.csv from a git hosting service

set +e

# Default configuration
REPOS_CSV="repos.csv"
REPOS_DIR="repos"
GIT_HOST="bitbucket.org"
ORG_NAME=""
USE_SSH=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --repos-csv)
            REPOS_CSV="$2"
            shift 2
            ;;
        --repos-dir)
            REPOS_DIR="$2"
            shift 2
            ;;
        --git-host)
            GIT_HOST="$2"
            shift 2
            ;;
        --org-name)
            ORG_NAME="$2"
            shift 2
            ;;
        --https)
            USE_SSH=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --repos-csv FILE    CSV file containing repository list (default: repos.csv)"
            echo "  --repos-dir DIR     Directory to clone repositories into (default: repos)"
            echo "  --git-host HOST     Git hosting service (default: bitbucket.org)"
            echo "  --org-name ORG      Organization/user name for repositories"
            echo "  --https             Use HTTPS instead of SSH"
            echo "  --help              Show this help message"
            echo ""
            echo "CSV file should have columns: repo_name,team,priority,notes"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$ORG_NAME" ]; then
    echo "❌ Error: --org-name is required"
    echo "Example: $0 --org-name myorg"
    exit 1
fi

# Check if CSV file exists
if [ ! -f "$REPOS_CSV" ]; then
    echo "❌ Repository CSV file '$REPOS_CSV' not found!"
    echo ""
    echo "Please create a CSV file with the following format:"
    echo "repo_name,team,priority,notes"
    echo "my-repo,backend,high,My Repository"
    echo "another-repo,frontend,medium,Another Repository"
    exit 1
fi

# Read repositories from CSV
echo "📁 Reading repositories from $REPOS_CSV..."
REPOSITORIES=()
while IFS=',' read -r repo_name team priority notes; do
    # Skip header line and empty lines
    if [[ "$repo_name" != "repo_name" && -n "$repo_name" ]]; then
        # Remove quotes and whitespace
        repo_name=$(echo "$repo_name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//')
        if [[ -n "$repo_name" ]]; then
            REPOSITORIES+=("$repo_name")
        fi
    fi
done < "$REPOS_CSV"

if [ ${#REPOSITORIES[@]} -eq 0 ]; then
    echo "❌ No repositories found in $REPOS_CSV"
    exit 1
fi

echo "📊 Found ${#REPOSITORIES[@]} repositories to clone"

# Create output directory
echo "📁 Creating directory: $REPOS_DIR"
mkdir -p "$REPOS_DIR"

# Test connectivity and authentication
echo ""
echo "🔍 Testing connectivity and authentication..."

if [ "$USE_SSH" = true ]; then
    echo "Testing SSH connection to $GIT_HOST..."
    if ssh -T "git@$GIT_HOST" -o ConnectTimeout=10 -o BatchMode=yes 2>/dev/null; then
        echo "✅ SSH connection successful"
        BASE_URL="git@$GIT_HOST:$ORG_NAME"
    else
        echo "❌ SSH connection failed, falling back to HTTPS"
        BASE_URL="https://$GIT_HOST/$ORG_NAME"
        USE_SSH=false
    fi
else
    echo "Using HTTPS authentication"
    BASE_URL="https://$GIT_HOST/$ORG_NAME"
fi

echo ""
echo "🚀 Starting clone of ${#REPOSITORIES[@]} repositories..."
echo "Host: $GIT_HOST"
echo "Organization: $ORG_NAME"
echo "Method: $([ "$USE_SSH" = true ] && echo "SSH" || echo "HTTPS")"
echo "Target directory: $REPOS_DIR"
echo "=" * 60

SUCCESS_COUNT=0
FAILED_REPOS=()

for repo in "${REPOSITORIES[@]}"; do
    printf "Cloning %-30s ... " "$repo"
    
    if [ -d "$REPOS_DIR/$repo" ]; then
        echo "already exists ⚠️"
        ((SUCCESS_COUNT++))
        continue
    fi
    
    CLONE_URL="$BASE_URL/$repo.git"
    
    if timeout 30 git clone "$CLONE_URL" "$REPOS_DIR/$repo" >/dev/null 2>&1; then
        echo "✅"
        ((SUCCESS_COUNT++))
    else
        echo "❌"
        FAILED_REPOS+=("$repo")
        
        # If SSH failed, try HTTPS as fallback
        if [ "$USE_SSH" = true ]; then
            printf "Retrying with HTTPS%-13s ... " ""
            HTTPS_URL="https://$GIT_HOST/$ORG_NAME/$repo.git"
            if timeout 30 git clone "$HTTPS_URL" "$REPOS_DIR/$repo" >/dev/null 2>&1; then
                echo "✅"
                ((SUCCESS_COUNT++))
                # Remove from failed list
                FAILED_REPOS=("${FAILED_REPOS[@]/$repo}")
            else
                echo "❌"
            fi
        fi
    fi
    
    # Brief pause to avoid overwhelming the server
    sleep 0.2
done

echo ""
echo "=" * 60
echo "📊 Cloning Summary:"
echo "   Successful: $SUCCESS_COUNT/${#REPOSITORIES[@]}"
echo "   Failed: ${#FAILED_REPOS[@]}"

if [ ${#FAILED_REPOS[@]} -gt 0 ]; then
    echo ""
    echo "❌ Failed repositories:"
    for repo in "${FAILED_REPOS[@]}"; do
        echo "   - $repo"
    done
    echo ""
    echo "💡 Common causes of failure:"
    echo "   • Repository doesn't exist or is private"
    echo "   • Authentication issues (SSH key not added or expired)"
    echo "   • Network connectivity problems"
    echo "   • Repository name mismatch"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   • For SSH: Ensure your SSH key is added to $GIT_HOST"
    echo "   • For HTTPS: You may need an app password or personal access token"
    echo "   • Verify repository names in $REPOS_CSV"
    echo "   • Check if you have access to the $ORG_NAME organization"
fi

echo ""
echo "🎉 Clone operation complete!"
echo "📁 Repositories cloned to: $REPOS_DIR"
echo ""
echo "💡 Next steps:"
echo "   1. Run the CI/CD analyzer:"
echo "      python3 cicd-analyzer.py --repos-dir '$REPOS_DIR' --repos-csv '$REPOS_CSV'"
echo "   2. Review the generated report"