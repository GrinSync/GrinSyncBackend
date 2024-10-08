# GrinSync
The Django backend for the GrinSync project. 

If you're already set up, check here for live API documentation: [https://documenter.getpostman.com/view/29620227/2sA35JzKYo](https://documenter.getpostman.com/view/29620227/2sA35JzKYo)

Otherwise, the info below will help you get started

## Repository Layout
- *api > tests.py*: The file with the testing classes for the backend. 
- *GrinSync*: Code to set up Django backend.

## Operational Use Cases ## 
- Register a new student user with email confirmation
- Forgot password?
- Log in after registration
- Link and create a student account to a student organization
- Create a new event (with repeating event options) - as an individual or as a student organization
- Edit an event you created (or an event in a student organization that you are linked to)
- Delete an event you created (or an event in a student organization that you are linked to)
- Follow a student organization
- Like an event
- Share an event
- Contact event host
- Search for events
- Filter events on the Home page
- View liked events, events I created, or preferred events on calendar (in various time views: monthly, weekly, daily) 
- Can view event details when clicking on an event
- Log out

## Coding
### Using the Linter
We use pylinter and the settings that are stored in `.pylintrc`. To get started, I'd recommend installing the pylinter extension for VSCode. From there you can use the command palette to run the linting server and you should be set. If you get an encoding error, __copy the existing config__, delete the file, and then run `pylint --generate-rcfile | out-file -encoding utf8 .pylintrc` before pasting the old config in place of the newly generated file

## Testing on a Local Machine
This is used for local development and testing changes before pushing code to production.

_Note:
For a Windows machine, it's great to know that [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) is an option that lets you run Linux commands. It might be a tad (depending on what you're doing) slower since it's just a VM running on Windows, so probably stick to the Windows-specific commands; I just love WSL and figured I'd give it a shoutout._

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

If you want to check the tests, you can use the following command, but if you're just pulling, the tests have been checked before push:

```
python manage.py test
```

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

You can test the API locally by installing Postman and using the [public workspace](https://www.postman.com/descent-module-operator-84099879/workspace/grinsyncworkspace/collection/29620227-3562082b-4020-4b32-8b28-3082ef7d8bfc?action=share&creator=29620227) we've set up for testing:
