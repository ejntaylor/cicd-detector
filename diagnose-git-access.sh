#!/bin/bash

# Git Access Diagnostic Script
# Helps diagnose authentication and connectivity issues with git hosting services

# Default configuration
GIT_HOST="bitbucket.org"
ORG_NAME=""
TEST_REPO=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --git-host)
            GIT_HOST="$2"
            shift 2
            ;;
        --org-name)
            ORG_NAME="$2"
            shift 2
            ;;
        --test-repo)
            TEST_REPO="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --git-host HOST     Git hosting service (default: bitbucket.org)"
            echo "  --org-name ORG      Organization/user name for repositories"
            echo "  --test-repo REPO    Repository name to test cloning"
            echo "  --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --git-host github.com --org-name myorg --test-repo myrepo"
            echo "  $0 --git-host gitlab.com --org-name mygroup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Git Access Diagnostic for $GIT_HOST"
echo "=" * 50
echo ""

# Test 1: Basic connectivity
echo "1. Testing basic connectivity to $GIT_HOST..."
if ping -c 3 "$GIT_HOST" >/dev/null 2>&1; then
    echo "   ✅ Can reach $GIT_HOST"
else
    echo "   ❌ Cannot reach $GIT_HOST (network issue)"
fi
echo ""

# Test 2: SSH connectivity
echo "2. Testing SSH connectivity..."
ssh_output=$(ssh -T "git@$GIT_HOST" -o ConnectTimeout=10 -o BatchMode=yes 2>&1)
ssh_exit_code=$?

if [ $ssh_exit_code -eq 0 ] || echo "$ssh_output" | grep -q "authenticated\|successfully authenticated"; then
    echo "   ✅ SSH authentication successful"
    if echo "$ssh_output" | grep -q "logged in as"; then
        echo "   User: $(echo "$ssh_output" | grep -o 'logged in as [^.]*' | cut -d' ' -f3)"
    fi
    SSH_WORKS=true
else
    echo "   ❌ SSH authentication failed"
    echo "   Output: $ssh_output"
    SSH_WORKS=false
fi
echo ""

# Test 3: SSH key presence
echo "3. Checking SSH keys..."
if ls ~/.ssh/id_* >/dev/null 2>&1; then
    echo "   ✅ SSH keys found:"
    ls -la ~/.ssh/id_* | awk '{print "     " $9 " (" $5 " bytes)"}'
    
    echo ""
    echo "   📋 Public keys:"
    for key in ~/.ssh/id_*.pub; do
        if [ -f "$key" ]; then
            echo "     $(basename "$key"):"
            echo "     $(cat "$key")"
            echo ""
        fi
    done
else
    echo "   ❌ No SSH keys found in ~/.ssh/"
    echo "   💡 Generate one with: ssh-keygen -t ed25519 -C 'your_email@example.com'"
fi
echo ""

# Test 4: SSH config
echo "4. Checking SSH config..."
if [ -f ~/.ssh/config ]; then
    if grep -q "$GIT_HOST" ~/.ssh/config; then
        echo "   ✅ $GIT_HOST configuration found in ~/.ssh/config"
        grep -A 5 -B 1 "$GIT_HOST" ~/.ssh/config | sed 's/^/     /'
    else
        echo "   ⚠️  SSH config exists but no $GIT_HOST configuration"
    fi
else
    echo "   ⚠️  No SSH config file found"
    echo "   💡 You can create ~/.ssh/config to customize SSH settings"
fi
echo ""

# Test 5: Git configuration
echo "5. Checking Git configuration..."
git_user=$(git config --global user.name)
git_email=$(git config --global user.email)

if [ -n "$git_user" ] && [ -n "$git_email" ]; then
    echo "   ✅ Git user configured:"
    echo "     Name: $git_user"
    echo "     Email: $git_email"
else
    echo "   ⚠️  Git user not fully configured"
    echo "     Name: ${git_user:-'NOT SET'}"
    echo "     Email: ${git_email:-'NOT SET'}"
    echo "   💡 Set with: git config --global user.name 'Your Name'"
    echo "      and: git config --global user.email 'your.email@example.com'"
fi
echo ""

# Test 6: Attempt to clone a repository
if [ -n "$ORG_NAME" ] && [ -n "$TEST_REPO" ]; then
    echo "6. Testing repository access..."
    temp_dir=$(mktemp -d)
    
    echo "   Testing SSH clone of $ORG_NAME/$TEST_REPO..."
    if [ "$SSH_WORKS" = true ]; then
        if git clone "git@$GIT_HOST:$ORG_NAME/$TEST_REPO.git" "$temp_dir/ssh-test" >/dev/null 2>&1; then
            echo "   ✅ SSH clone successful"
            rm -rf "$temp_dir/ssh-test"
            CLONE_METHOD="SSH"
        else
            echo "   ❌ SSH clone failed"
            CLONE_METHOD="NONE"
        fi
    else
        echo "   ⏭️  Skipping SSH clone (authentication failed)"
        CLONE_METHOD="NONE"
    fi
    
    echo "   Testing HTTPS clone of $ORG_NAME/$TEST_REPO..."
    if git clone "https://$GIT_HOST/$ORG_NAME/$TEST_REPO.git" "$temp_dir/https-test" >/dev/null 2>&1; then
        echo "   ✅ HTTPS clone successful"
        rm -rf "$temp_dir/https-test"
        if [ "$CLONE_METHOD" = "NONE" ]; then
            CLONE_METHOD="HTTPS"
        fi
    else
        echo "   ❌ HTTPS clone failed (likely private repository or no access)"
    fi
    
    rm -rf "$temp_dir"
    echo ""
else
    echo "6. Repository testing skipped (no --org-name or --test-repo provided)"
    echo ""
    CLONE_METHOD="UNKNOWN"
fi

# Summary and recommendations
echo "SUMMARY & RECOMMENDATIONS"
echo "=" * 50
echo ""

case "$CLONE_METHOD" in
    "SSH")
        echo "✅ Ready to clone! SSH method working:"
        if [ -n "$ORG_NAME" ]; then
            echo "   ./clone-repos.sh --git-host '$GIT_HOST' --org-name '$ORG_NAME'"
        else
            echo "   SSH authentication is working properly"
        fi
        ;;
    "HTTPS")
        echo "⚠️  SSH not working, but HTTPS might work with authentication:"
        if [ -n "$ORG_NAME" ]; then
            echo "   ./clone-repos.sh --git-host '$GIT_HOST' --org-name '$ORG_NAME' --https"
        fi
        echo ""
        echo "To fix SSH access:"
        echo "   1. Add your SSH key to $GIT_HOST"
        echo "   2. Copy your public key: cat ~/.ssh/id_ed25519.pub"
        case "$GIT_HOST" in
            "github.com")
                echo "   3. Add it at: https://github.com/settings/ssh"
                ;;
            "bitbucket.org")
                echo "   3. Add it at: https://bitbucket.org/account/settings/ssh-keys/"
                ;;
            "gitlab.com")
                echo "   3. Add it at: https://gitlab.com/-/profile/keys"
                ;;
            *)
                echo "   3. Add it to your $GIT_HOST SSH keys settings"
                ;;
        esac
        ;;
    "NONE"|"UNKNOWN")
        echo "❌ Issues detected. Possible problems:"
        echo "   • Repository is private and you don't have access"
        echo "   • SSH key not added to $GIT_HOST"
        echo "   • Network/firewall blocking connections"
        echo "   • Incorrect organization/repository names"
        echo ""
        echo "Steps to fix:"
        echo "   1. Verify you have access to the repositories"
        echo "   2. Add SSH key to $GIT_HOST"
        echo "   3. For HTTPS, you may need an app password or personal access token"
        echo ""
        echo "Host-specific links:"
        case "$GIT_HOST" in
            "github.com")
                echo "   • SSH keys: https://github.com/settings/ssh"
                echo "   • Personal access tokens: https://github.com/settings/tokens"
                ;;
            "bitbucket.org")
                echo "   • SSH keys: https://bitbucket.org/account/settings/ssh-keys/"
                echo "   • App passwords: https://bitbucket.org/account/settings/app-passwords/"
                ;;
            "gitlab.com")
                echo "   • SSH keys: https://gitlab.com/-/profile/keys"
                echo "   • Access tokens: https://gitlab.com/-/profile/personal_access_tokens"
                ;;
        esac
        ;;
esac

if [ -n "$ORG_NAME" ] && [ -z "$TEST_REPO" ]; then
    echo ""
    echo "💡 For more specific testing, provide a test repository:"
    echo "   $0 --git-host '$GIT_HOST' --org-name '$ORG_NAME' --test-repo 'repo-name'"
fi