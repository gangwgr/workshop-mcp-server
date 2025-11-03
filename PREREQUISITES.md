# Prerequisites

## Required

- **Python 3.8+** (3.9+ recommended)
- **pip** - Python package manager
- **Git** - Version control

## Optional (Feature-Specific)

### For GitHub PR Review
- **GitHub CLI (`gh`)** - Install from https://cli.github.com/

### For OpenShift Features
- **OpenShift CLI (`oc`)** - Install from https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html
- **OpenShift Cluster Access** - Version 4.8+
- **Kubeconfig file** configured

### For Web GUI
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

---

## Installation Instructions

### Python 3.8+

```bash
# macOS (via Homebrew)
brew install python@3.9

# Linux (Ubuntu/Debian)
sudo apt update && sudo apt install python3.9 python3-pip

# Linux (RHEL/CentOS)
sudo yum install python39 python39-pip

# Verify
python3 --version
```

### GitHub CLI (gh)

```bash
# macOS
brew install gh

# Linux
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y

# Windows
winget install --id GitHub.cli

# Authenticate
gh auth login
```

### OpenShift CLI (oc)

```bash
# Download from OpenShift mirror
curl -LO https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz
tar xvzf openshift-client-linux.tar.gz
sudo mv oc /usr/local/bin/
sudo chmod +x /usr/local/bin/oc

# Verify
oc version

# Login to cluster
oc login https://api.your-cluster.example.com:6443
```

---

## Verification Checklist

Run these commands to verify your setup:

```bash
✅ python3 --version          # Should show 3.8+
✅ pip --version              # Should be installed
✅ git --version              # Should be installed
✅ gh --version               # (Optional) For PR review
✅ oc version                 # (Optional) For OpenShift features
✅ oc whoami                  # (Optional) Verify cluster login
```

---

## Troubleshooting

**Python not found?**
- Ensure Python 3.8+ is in your PATH
- Try `python` instead of `python3`

**GitHub CLI auth fails?**
- Run `gh auth login` and follow prompts
- Generate personal access token: https://github.com/settings/tokens

**OpenShift CLI connection fails?**
- Verify cluster URL is correct
- Check kubeconfig: `export KUBECONFIG=/path/to/kubeconfig`
- Verify network access to cluster

---

**Ready?** Proceed to [SETUP.md](SETUP.md) for installation.
