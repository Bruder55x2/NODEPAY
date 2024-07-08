# NodePlay-Termux

to run the code, you need to install the following packages:

```bash
git clone https://github.com/pranavkdileep/NodePlay-Termux
cd NodePlay-Termux
pip install -r requirements.txt
```

## Configuration

#Get NP_TOKEN
1. Go to [NodePlay](https://app.nodepay.ai/register?ref=veSvPdiRAekyAXq)
2. Sign in with your account
3.Inspect Element and go to the Console tab
4. Type `localStorage.getItem('np_token');` and press Enter

#Add NP_TOKEN to the code
1. Open `nodeplay.py` in a text editor
2. Replace NP_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjEwMjIwNzY' with your NP_TOKEN

## Usage

```bash
python3 nodeplay.py
```