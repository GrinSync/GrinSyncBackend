"""
This file creates a command that can be run from the command line. It scrapes events from Grinnell's live
calendar via API and is run by cron on the server every night.
"""
import datetime
import json
import re
import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from requests import get

from api.aux_functions import addEventTags
from api.models import Event, User

CST = pytz.timezone('America/Chicago')

autoPopulateUser = User.objects.get(username="moderator")

# RSS_URL = "https://events.grinnell.edu/live/rss/events"

# def checkGrinnellTerms(body):
#     body = body.lower()
#     # If we implment this for additional tags, we'll want to make it editable in admin settings
#     validTerms = ['hssc', 'humanities and social science', 'noyce', 'jrc', 'rosenfield center', 'burling',
#                   'bucksbaum', 'steiner', 'crssj', 'forum', 'kington', 'harris', 'herrick', 'main hall',
#                   'cleveland', 'younker', 'smith', 'langan', 'rawson', 'gates', 'clark', 'cowles', 'dibble',
#                   'norris', 'loose', 'read', 'haines', 'lazier', 'kershaw', 'rose', 'rathje', 'james hall',
#                   'bear', 'charles benson', 'brac', 'rosenbloom', 'osgood', 'young track', 'darby',
#                   'grinnell', 'ahrens', 'rock creek', 'arbor lake', 'central park', 'stew']

#     for term in validTerms:
#         if term in body:
#             return True
#     return False


def checkCommonGrinnellLocations(loc_name):
    """ Checks a location string for common location names and returns the coordinates of that place if on record. """
    loc_name = loc_name.lower()
    knownLocations = [(['hssc', 'humanities and social science'] , (41.750897, -92.72107)),
                        (['noyce'],(41.748778, -92.720069)),
                        (['jrc', 'rosenfield center'],(41.74929, -92.720118)),
                        (['burling'],(41.74672, -92.720287)),
                        (['bucksbaum'],(41.746485, -92.721170)),
                        (['steiner'],(41.747309, -92.722076)),
                        (['crssj'],(41.749286, -92.723188)),
                        (['forum'],(41.74748, -92.720104)),
                        (['kington'],(41.748449, -92.721456)),
                        (['harris'],(41.751082, -92.720641)),
                        (['herrick'],(41.747604, -92.722204)),
                        (['main hall'],(41.74664, -92.718331)),
                        (['bear', 'charles benson', 'brac', 'darby'],(41.752130, -92.719527)),
                        (['rosenbloom','football field', 'stride field'], (41.75318, -92.719881)),
                        (['osgood', 'natatorium'],(41.752342, -92.720638)),
                        (['track'],(41.752342, -92.720638)),
                        (['tennis courts'],(41.752765, -92.718050)),
                        (['central park'],(41.74238, -92.723181)),
                        (['stew'],(41.744202, -92.724325))
                     ]

    for terms, coords in knownLocations:
        if any(x in loc_name for x in terms):
            return coords

    return (None, None)

#pylint: disable=C0301
#JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/near_location/8421/near_distance/10/paginate/false"
#JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/near_location/8421/near_distance/10"
JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/paginate/"
# JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all"


def scrapeCalendar(num_events = "false"):
    """ Scrapes Grinnell's events JSON feed """
    url =JSON_URL + str(num_events)
    events = json.loads(get(url, timeout=20).text)['data']

    # Process the events
    for event in events: # TODO: Add filtering for intended audience (at least make sure it's not profs)
                         # And by location. And add tags for student orgs
        title = event['title'].strip().replace('&amp;','&') # Replace the HTML & with &
        startTime = datetime.datetime.strptime(event['date_utc'], "%Y-%m-%d %H:%M:%S")
        startTime = pytz.utc.localize(startTime) # Make it timezone aware
        if event['date2_utc']:
            endTime = datetime.datetime.strptime(event['date2_utc'], "%Y-%m-%d %H:%M:%S")
            endTime = pytz.utc.localize(endTime)
        else:
            endTime = startTime + datetime.timedelta(hours = 1) # If we don't know the end time, assume lasts an hour

        if event['location_title']:
            location = event['location_title']
        else:
            location = event['location']

        if not location: # The calendar contains all day non-location holidays and stuff that aren't really *events*
            continue

        location = location.replace('&#160;','').replace('&amp;','&')
        if event['location_latitude'] and event['location_longitude']:
            lat = event['location_latitude']
            long = event['location_longitude']
        else:
            # Check the lookup table for different common locations
            lat, long = checkCommonGrinnellLocations(location) # TODO: Does this check for home vs away? No, but looks like the away are usually just names of the city

        if event['description']:
            description = event['description'].strip() # We won't clear the html here cause we're rendering it on the frontend
        else:
            description = "" #pylint: disable=C0103

        externalID = event['id'] # Record the livewhale ID so we can avoid duplicates later

        # Get the existing tags
        tags = set()
        if event['tags']:
            temp = list(map(lambda x: x.replace('Student Activity', 'Student Activities'), event['tags']))
            tags.update(temp)
        if event['event_types']:
            tags.update(event['event_types'])
        tags = list(tags)

        # People don't give a shit about tabling, but instead of just kicking them out, we'll tag them
        if ('tabling' in title.lower()) or ('tabling' in description.lower()):
                        # Idk, is it possible some don't have a title? Prob not
            tags.append('Tabling')

        # Same with SCL or mentor seshs
        terms = ['mentor session', "scl "]
        if any(x in title.lower() for x in terms) or any(x in description.lower() for x in terms):
            tags.append('Mentor Session')
            try:
                tags.remove('Student Activities') # We don't want them to fall in with regular activities
            except ValueError:
                pass

        # This is for letting us claim events and implement contacting event hosts
        if 'contact_info' in event:
            contactEmail = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', event['contact_info']).group(0).lower()
        elif 'registration_owner_email' in event:
            contactEmail = event['registration_owner_email']
        else:
            contactEmail = None


        # Now we do the actual updating. We don't use get_or_create because I was too lazy to figure out what was broken
        try:
            event = Event.objects.get(liveWhaleID = externalID)
            if event.host != autoPopulateUser: # We want to avoid changing them if someone has claimed it
                continue

            Event.objects.filter(liveWhaleID = externalID).update(
                                    host = autoPopulateUser, title = title,
                                    location = location, start = startTime, end = endTime,
                                    description = description, studentsOnly = False,
                                    liveWhaleID = externalID, contactEmail = contactEmail,
                                    lat = lat, long = long)

            event = Event.objects.get(liveWhaleID = externalID)
        except ObjectDoesNotExist: # If there's nothing with that LiveWhale ID, that means we don't have this event yet

            # Ok clearly the livewhale filtering alone wasn't enough since there's lots of duplicates all over the place.
                # Seems like the college often updates events/puts two down for rain locations and those have different IDS
            ## TODO: Support Rain/Alt Locations
            matches = Event.objects.filter(host = autoPopulateUser, title = title, start = startTime, end = endTime)
            if matches.count() == 1:
                # Idk this just is the best I can think of. If something's wrong, they can make an account
                if any(x in description.lower() for x in [" overflow ", " rain "]):
                    description = matches[0].description
                if location != matches[0].location:
                    if not Event.objects.filter(pk__gt = matches[0].pk).exists(): # If the match is the most recent, it's likely it's an alternative, if it's not then it might be a revision
                        description += f"\n<br><i>Potential Alternative/Rain Location Automatically Detected: {location}</i>"
                        matches.update(host = autoPopulateUser, title = title, start = startTime, end = endTime,
                                        description = description, studentsOnly = False,
                                        contactEmail = contactEmail,
                                        lat = lat, long = long)
                    else:
                        description = description + str(f"\n<br><i>Potential Alternative/Rain Location Automatically Detected: {matches[0].location}</i>"),
                        matches.update(host = autoPopulateUser, title = title, start = startTime, end = endTime,
                                        location = location, description = description, studentsOnly = False,
                                        liveWhaleID = externalID, contactEmail = contactEmail,
                                        lat = lat, long = long)
                else:
                    matches.update(host = autoPopulateUser, title = title, start = startTime, end = endTime,
                                    description = description, studentsOnly = False,
                                    liveWhaleID = externalID, contactEmail = contactEmail,
                                    lat = lat, long = long)
                continue
            elif matches.count() >= 1:
                continue

            event = Event.objects.create(host = autoPopulateUser, title = title,
                                    location = location, start = startTime, end = endTime,
                                    description = description, studentsOnly = False, # I'm going to assume thats
                                        # if it was on the college's public calendar, we don't need to hide it
                                        # but also I know not all are, so maybe find a clever way to do this
                                    liveWhaleID = externalID, contactEmail = contactEmail,
                                    lat = lat, long = long)
        addEventTags(event, tags, create_new = True)


## This is what allows us to run this as a command from the console. The command name is the filename
class Command(BaseCommand):
    """ The wraper to run this command from the terminal """
    help = "Scrapes Grinnell's events calendar and adds them to GrinSync's database"

    def handle(self, *args, **options):
        scrapeCalendar()
