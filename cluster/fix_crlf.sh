#!/bin/bash
# Naprawia Windows line endings (CRLF -> LF) we wszystkich skryptach
# Uruchom raz po skopiowaniu z Windows na klaster:
#   bash fix_crlf.sh

cd "$(dirname "$0")"

echo "Fixing CRLF line endings..."

for f in *.sh *.sbatch scripts/*.py mdp/*.mdp; do
    if [[ -f "$f" ]]; then
        sed -i 's/\r$//' "$f"
        echo "  Fixed: $f"
    fi
done

echo "Done!"
