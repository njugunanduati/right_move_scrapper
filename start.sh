#!/bin/bash

if [ ! -d "renv" ]; then
  	echo "Creating a virtual enviroment"
	python3 -m venv  renv
fi
echo "Activating the virtual enviroment"
source renv/bin/activate

echo "Starting the server"
python index.py

#pip install --upgrade pip

#pip install -r requirements.txt

