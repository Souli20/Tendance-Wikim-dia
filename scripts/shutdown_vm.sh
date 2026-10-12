#!/usr/bin/env bash
bash "$HOME/Projet_Big_Data/scripts/stop_all.sh"
sudo systemctl stop mongod
echo "Arrêt de la VM dans 5 secondes (Ctrl+C pour annuler)"
sleep 5
sudo poweroff
