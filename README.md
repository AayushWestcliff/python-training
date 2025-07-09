# Python Training

### Cloning all student's repo

```bash
gh repo list Kings-Python-Training --json name --jq '.[] | select(.name | startswith("project-")).name' | while read -r repo; do git clone github.com-Aayush181509:Kings-Python-Training/$repo.git; done
```

