# Dev container setup

The dev container is self-sufficient: open the folder in VS Code, choose
**Reopen in Container**, and everything needed to develop the library is built
automatically.

The only part that requires a **one-time manual setup on each new machine** is
SSH commit signing, described below.

## SSH commit signing (one-time per machine)

Commits are signed with an SSH key that lives on the **host** machine (the WSL
distro on Linux/Windows, or macOS itself). The container reads the key through
a read-only bind mount of `~/.ssh` (see `mounts` in `devcontainer.json`), and
VS Code copies the host `~/.gitconfig` into the container automatically, so all
configuration below is done **on the host, outside the container**.

Run these steps in a host terminal (WSL shell or macOS Terminal):

```bash
# 1. Generate a signing key, if ~/.ssh/id_ed25519 does not exist yet
ssh-keygen -t ed25519 -C "<your-github-email>"

# 2. Upload the public key to GitHub as a SIGNING key (not an authentication key)
gh auth refresh -h github.com -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/id_ed25519.pub --type signing --title "<name-of-this-machine>"
# Alternatively: GitHub → Settings → SSH and GPG keys → New SSH key → key type "Signing Key"

# 3. Configure git to sign every commit with that key
#    Quotes matter: git must store the literal ~ so the path resolves to the
#    right home directory both on the host and inside the container.
git config --global gpg.format ssh
git config --global user.signingkey '~/.ssh/id_ed25519.pub'
git config --global commit.gpgsign true

# 4. Register your key as an allowed signer, so that signature VERIFICATION
#    (git log --show-signature) also works locally. Signing alone does not
#    need this, but the verification step below does. The file lives in
#    ~/.ssh so the container sees it through the same mount.
awk '{print "<your-github-email> "$1" "$2}' ~/.ssh/id_ed25519.pub >> ~/.ssh/allowed_signers
git config --global gpg.ssh.allowedSignersFile '~/.ssh/allowed_signers'
```

Then (re)build the container (**Dev Containers: Rebuild Container**) and verify
from a terminal *inside* the container:

```bash
git commit --allow-empty -m "signing test"
git log --show-signature -1   # must show: Good "git" signature for <email> ...
git reset --hard HEAD~1       # drop the test commit
```

### Notes and troubleshooting

- **Order matters**: `~/.ssh` must exist on the host *before* the container is
  (re)built, otherwise Docker creates the mount source itself, owned by root.
  If that happened, fix it on the host with
  `sudo chown -R $USER:$USER ~/.ssh && chmod 700 ~/.ssh`.
- **"key not found" / "failed to sign" on commit**: the key is missing on the
  host side of the mount, or the container was built before the key existed.
  Re-run step 1, then rebuild the container.
- **"No signature" from `git log --show-signature` (with an error about
  `gpg.ssh.allowedSignersFile`)**: the commit is usually signed just fine —
  git only lacks the allowed-signers file needed to *verify* it. Complete
  step 4 on the host. GitHub verification is unaffected either way; it uses
  the key uploaded in step 2.
- Use a **separate key per machine** (do not copy private keys around): if a
  machine is ever compromised, revoke only its key on GitHub.
- Optional hardening: enable **vigilant mode** on GitHub
  (Settings → SSH and GPG keys → *Flag unsigned commits*) so any unsigned
  commit claiming your email shows up as "Unverified".
- **Post-quantum note**: Ed25519 is not quantum-safe, but as of July 2026 it is
  still the right choice — GitHub does not accept post-quantum signing keys
  yet, and OpenSSH's composite scheme (`ssh-keygen -t mldsa44-ed25519`,
  ML-DSA-44 + Ed25519, introduced as experimental in OpenSSH 10.4) is not
  standardized. When GitHub starts accepting post-quantum signing keys,
  rotate: generate a new key with the composite type and repeat steps 2-3.
