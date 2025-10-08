# HRI

This project is a Flask web application for drawing and processing images.  
Follow the steps below to set up a virtual environment, install dependencies, and run the server.

---

## 1. Clone the Repository
```bash
git clone https://github.com/lyjosh/HRI.git
cd HRI



Powershell
python -m venv venv
venv\Scripts\Activate

MacOS

brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
python --version   # should say 3.11.x
pip install --upgrade pip setuptools wheel

Install Dependencies:
pip install --upgrade pip
pip install -r requirements.txt

To Run:
flask run

After creating your venv, to reactivate in another terminal, use:
source venv/bin/activate

to exit the virtual environment use: 
deactivate
