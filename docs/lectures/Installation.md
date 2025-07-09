## **Installation Setup Guide**

Quick setup for Python development with Git and VS Code.

### What We'll Install:

- **Python** - Programming language

- **Git** - Version control 

- **SSH Keys** - Secure authentication

- **VS Code** - Code editor

---

## **Python Installation**

### 🪟 Windows
1. Go to https://www.python.org/downloads/

2. Click "Download Python 3.x.x"

3. Run the installer

4. **Check "Add Python to PATH"**

5. Click "Install Now"

**If needed, run this command in PowerShell as Administrator:**

```powershell

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

```

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 🍎 macOS
```bash
# Install Homebrew first if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

**Verify installation:**
```bash
python --version
pip --version
```

---

## **Git Installation & Setup**

### Install Git

**🪟 Windows:** Download from https://git-scm.com/download/win and install

**🐧 Linux:**
```bash
sudo apt install git
```

**🍎 macOS:**
```bash
brew install git
```

### Configure Git
```bash
git config --global user.name "GithubUsername"
git config --global user.email "your.email@example.com"
```

### Setup SSH Key
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Test connection
ssh -T git@github.com
```

**Add your SSH key to GitHub:**

1. Copy the public key: `cat ~/.ssh/id_ed25519.pub` 

      - *C:\Users\path\.ssh\id_ed25519.pub*(For Windows)

2. Go to GitHub Settings → SSH Keys

3. Paste and save

---

## **VS Code Setup**

### Install VS Code
1. Go to https://code.visualstudio.com/

2. Download for your operating system

3. Install with default settings

### Essential Extensions

Install these extensions for Python development:

- **Python** (Microsoft)

- **Pylance** (Microsoft)

- **Python Extension Pack** (Microsoft)

- **GitLens** (GitKraken)

- **Jupyter** (Microsoft)

**How to install extensions:**

1. Open VS Code

2. Click Extensions icon (squares) on left sidebar

3. Search for extension name

4. Click "Install"

---

## **Virtual Environment Setup**

### Create Virtual Environment
```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# Windows:
env\Scripts\activate

# Linux/macOS:
source env/bin/activate
```

### Install Packages in Virtual Environment
```bash
# After activating virtual environment
pip install uv

uv pip install ipykernel numpy pandas matplotlib

# To deactivate virtual environment
deactivate
```

---

## **Jupyter Notebooks in VS Code**

### Create Jupyter Notebook in VS Code
1. Open VS Code

2. Create new file: `Ctrl+N` (Windows/Linux) or `Cmd+N` (Mac)

3. Save as `.ipynb` file: `Ctrl+S` → name it `test.ipynb`

4. VS Code will automatically open it as a Jupyter notebook

### Select Python Kernel

1. Click "Select Kernel" in top-right of notebook

2. Choose "Python Environments"

3. Select your virtual environment or system Python

4. Start coding in cells!

### Basic Usage

- **Add cell**: Click `+ Code` or `+ Markdown`

- **Run cell**: `Shift+Enter` | `Alt+Enter` | `Ctrl+Enter`

- **Run all cells**: `Ctrl+Shift+P` → "Run All Cells"

---

## **Test Your Setup**

Run these commands to verify everything works:

**Test in terminal:**
```bash
# Check Python
python --version

# Check Git  
git --version

# Check Git config
git config --global --list

# Test SSH connection to GitHub
ssh -T git@github.com

# Test virtual environment
python -m venv test_env
# Windows: test_env\Scripts\activate
# Linux/macOS: source test_env/bin/activate

# Test creating .ipynb file in VS Code
# 1. Open VS Code
# 2. Create new file (Ctrl+N)
# 3. Save as test.ipynb
# 4. Select Python kernel
# 5. Start coding!
```

**You're ready to start coding!**
