#!/bin/bash

# Prüfen ob python3 installiert ist
if ! command -v python3 &> /dev/null; then
	echo "python3 ist nicht installiert. Bitte installieren."
	exit 1
fi

# Prüfen ob venv Modul vorhanden ist
if ! python3 -c "import venv" &> /dev/null; then
	echo "Python venv Modul ist nicht installiert."
	exit 1
fi

# Prüfen ob pip installiert ist
if ! python3 -m pip --version &> /dev/null; then
	echo "pip ist nicht installiert. Bitte installieren."
	exit 1
fi

VENV_DIR="$HOME/website_visitor_venv"

# Prüfen ob venv existiert, wenn nicht, erstellen
if [ ! -d "$VENV_DIR" ]; then
	echo "Erstelle virtual environment in $VENV_DIR"
	python3 -m venv "$VENV_DIR"
fi

# venv aktivieren
source "$VENV_DIR/bin/activate"

# Installieren der requirements falls noch nicht installiert
if [ -f "requirements.txt" ]; then
	# Liste der installierten Pakete
	INSTALLED=$(pip freeze)

  # Pakete aus requirements.txt, die noch nicht installiert sind, herausfiltern
  TO_INSTALL=$(comm -23 <(sort requirements.txt) <(echo "$INSTALLED" | sort) | tr '\n' ' ')

  if [ -n "$TO_INSTALL" ]; then
	  echo "Installiere Pakete, falls nicht installiert: $TO_INSTALL"
	  pip install -q $TO_INSTALL
  else
	  echo "Alle Pakete sind bereits installiert."
  fi
else
	echo "Keine requirements.txt gefunden."
fi

# Python Script mit allen übergebenen Parametern starten
python3 website_visitor.py "$@"
