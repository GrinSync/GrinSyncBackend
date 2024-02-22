### GrinSync
# Backend - Django over PostgreSQL

The backend for the GrinSync project. 


## Testing on a Local Machine
This is used for local development and testing changes before pushing code to production.

_Note:
For a Windows machine, you could use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) to run Linux-style commands. Although, this might cause processes to slow down since your repository does not live under your WSL installation. It is recommended that you use the Windows-specific commands._

### Step 0: Create a virtualenv

_Note: This is not strictly necessary. However, it is a standard to use virtual environments because of the way `pip` manages dependencies._

#### Install `virtualenv`

MacOS/Linux:

```
sudo apt-get install python-virtualenv
```

Windows:

```
pip install virtualenv
```

#### Create virtual environment

```
virtualenv venv
```

#### Activate virtual environment

MacOS/Linux:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate
```

### Step 1: Install Required Dependencies

Install the required dependencies:

```
python -m pip install -r requirements.txt
```



### Step 2 (for now, since there's not really any thing there): Start up the server

Run server with:

```
python manage.py runserver
```

### Step 3: (Optional) If you want to test admin stuff
_This doesn't really matter right now, but it'll be good know for later_

Create admin user with:

```
python manage.py createsuperuser
```
