# Ansible Collection - jonzeolla.labs

This is an Ansible collection used for Jon Zeolla's labs.

## Roles

The install roles are built for golden images: tools land machine-wide, because a lab or streamed session usually runs as a different user than the one
converging the image, and versions are pinned in each role's `defaults/main.yml` with self-updaters and update checks turned off, so the image is rebuilt
to update rather than drifting after it is taken.

| Role | Installs | Platforms |
| --- | --- | --- |
| `chromium` | Chromium, from EPEL | RedHat |
| `claude_code` | Claude Code, from npm (depends on `nodejs`) | RedHat, Windows |
| `cloud9` | AWS Cloud9 environment setup | Linux |
| `codex` | OpenAI Codex CLI, from npm (depends on `nodejs`) | RedHat, Windows |
| `docker` | Docker Engine | Debian, RedHat |
| `docker_compose` | Docker Compose | Debian, RedHat |
| `docker_registry` | A local Docker registry | Debian, RedHat |
| `git` | Git | Linux, Windows |
| `gitlab` | GitLab | Debian, RedHat |
| `gitlab_runner` | GitLab Runner | Debian, RedHat |
| `homebrew` | Homebrew | Debian, RedHat |
| `nodejs` | Node.js and npm (AppStream module stream on RedHat, pinned MSI on Windows) | RedHat, Windows |
| `ollama` | Ollama | Debian, RedHat |
| `pi` | Pi coding agent, from npm (depends on `nodejs`) | RedHat, Windows |
| `uv` | uv | Linux |
| `vscode` | Visual Studio Code, from Microsoft's RPM repository | RedHat |
| `zenable_cli` | Zenable CLI | Linux, Windows |

## Usage

```yaml
- name: Coding agents
  ansible.builtin.include_role:
    name: "jonzeolla.labs.{{ agent }}"
  loop: [claude_code, codex, pi]
  loop_control:
    loop_var: agent

# GUI apps can also drop a launcher on named users' desktops and in /etc/skel
- name: Editor
  ansible.builtin.include_role:
    name: jonzeolla.labs.vscode
  vars:
    vscode_launcher_users: [lab-user]
    vscode_launcher_in_skel: true
```
