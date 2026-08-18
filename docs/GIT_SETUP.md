# GitHub — setup su più PC (casa + lavoro)

Questa guida risolve i problemi più comuni su Windows:

- `Authentication failed`
- `Repository not found`
- `could not read Username for 'https://github.com'`
- token `ghp_` non accettato / doppio prefisso
- `git pull` che chiede password ogni volta

**Regola d'oro:** non incollare mai il token nell'URL del remote. Usa **GitHub CLI** o **SSH**.

---

## Metodo consigliato — GitHub CLI (`gh`)

Funziona allo stesso modo su **PC casa** e **PC lavoro**. Ogni PC fa login una volta.

### 1. Installa Git + GitHub CLI

- Git: https://git-scm.com/download/win
- GitHub CLI: https://cli.github.com/

Verifica:

```powershell
git --version
gh --version
```

### 2. Login GitHub (su ogni PC, una volta)

```powershell
gh auth login
```

Scegli:

| Domanda | Risposta |
|---------|----------|
| Account | `GitHub.com` |
| Protocol | `HTTPS` |
| Authenticate | `Login with a web browser` |
| Git credentials | `Yes` |

Si apre il browser → autorizza → torna al terminale.

Verifica:

```powershell
gh auth status
git ls-remote https://github.com/Michael98sanna/Alpilab-ai.git HEAD
```

Se vedi un hash commit → **GitHub funziona**.

### 3. Clone (prima volta su un PC)

```powershell
cd C:\Users\michael\Desktop
gh repo clone Michael98sanna/Alpilab-ai
cd Alpilab-ai
git checkout cursor/pc-agent-v0-4
```

### 4. Aggiornare (ogni volta che cambi PC)

```powershell
cd C:\Users\michael\Desktop\Alpilab-ai
git fetch origin
git checkout cursor/pc-agent-v0-4
git pull origin cursor/pc-agent-v0-4
```

---

## Metodo alternativo — SSH (senza token in chiaro)

Utile se il PC lavoro blocca il login browser.

### 1. Genera chiave (su ogni PC, una volta)

```powershell
ssh-keygen -t ed25519 -C "michael-alpilab-pc-lavoro" -f "$env:USERPROFILE\.ssh\id_ed25519_alpilab"
```

Premi Invio per passphrase vuota (o impostane una).

### 2. Aggiungi chiave a GitHub

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_alpilab.pub" | Set-Clipboard
```

GitHub → **Settings → SSH and GPG keys → New SSH key** → incolla → salva.

Ripeti su **PC casa** con un nome diverso (es. `michael-alpilab-pc-casa`).

### 3. Config SSH (`~/.ssh/config`)

```powershell
notepad $env:USERPROFILE\.ssh\config
```

Contenuto:

```text
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_alpilab
  IdentitiesOnly yes
```

### 4. Clone via SSH

```powershell
git clone git@github.com:Michael98sanna/Alpilab-ai.git
cd Alpilab-ai
git checkout cursor/pc-agent-v0-4
```

---

## Se il repo esiste già ma GitHub non funziona

### A. Pulisci credenziali vecchie (causa #1 su Windows)

```powershell
# Rimuovi token/password GitHub salvati male
cmdkey /list | findstr git
```

Se vedi voci `git:https://github.com`:

```powershell
cmdkey /delete:LegacyGeneric:target=git:https://github.com
```

Poi rifai:

```powershell
gh auth login
```

### B. Correggi remote (niente token nell'URL)

```powershell
cd C:\Users\michael\Desktop\Alpilab-ai
git remote -v
git remote set-url origin https://github.com/Michael98sanna/Alpilab-ai.git
```

**Non usare** URL tipo:
`https://ghp_xxxxx@github.com/...` ← causa errori e token esposto.

### C. Verifica accesso

```powershell
gh auth status
git fetch origin
```

---

## Configurazione Git consigliata (Windows)

Esegui una volta per PC:

```powershell
git config --global user.name "Michael Sanna"
git config --global user.email "sannamichael82@gmail.com"
git config --global init.defaultBranch main
git config --global core.autocrlf true
git config --global pull.rebase false
git config --global credential.helper manager
```

---

## Branch da usare per i test V0.4

```powershell
git checkout cursor/pc-agent-v0-4
git pull origin cursor/pc-agent-v0-4
```

Ultimo commit atteso (V0.4 + script test): controlla con:

```powershell
git log -1 --oneline
```

---

## Workflow casa ↔ lavoro

```text
PC A (casa)                    GitHub                    PC B (lavoro)
    │                             │                          │
    │  git push                     │                          │
    ├────────────────────────────►│                          │
    │                             │  git pull                  │
    │                             │◄───────────────────────────┤
    │                             │                          │
    │  git pull                     │  git push                  │
    │◄────────────────────────────┤───────────────────────────►│
```

**Sempre prima di lavorare:**

```powershell
git pull origin cursor/pc-agent-v0-4
```

**Prima di cambiare PC:**

```powershell
git add -A
git commit -m "descrizione"
git push origin cursor/pc-agent-v0-4
```

---

## Errori frequenti

| Errore | Soluzione |
|--------|-----------|
| `Authentication failed` | `cmdkey /delete` + `gh auth login` |
| `Repository not found` | Repo privato senza auth → `gh auth login` |
| `Updates were rejected` | `git pull` prima di `git push` |
| `No module named pc_agent` | Sei fuori cartella repo → `cd Alpilab-ai` |
| Token `ghp_` rifiutato | Non usarlo come password; usa `gh auth login` |
| Doppio `ghp_ghp_` | Remote con token nell'URL → `git remote set-url` pulito |

---

## Clone senza Git (emergenza)

Se Git non funziona affatto:

1. Apri https://github.com/Michael98sanna/Alpilab-ai
2. Branch `cursor/pc-agent-v0-4`
3. **Code → Download ZIP**
4. Estrai in `Desktop\Alpilab-ai`

Per i test va bene, ma **non puoi pushare** finché non sistemi Git.

---

## Script automatico Windows

Dalla root repo:

```powershell
.\scripts\setup_git_windows.ps1
```
