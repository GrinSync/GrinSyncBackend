import datetime
import json
import string
import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from requests import get

from api.models import Event, Tag, User

CST = pytz.timezone('America/Chicago')

autoPopulateUser = User.objects.get(username="moderator")

# RSS_URL = "https://events.grinnell.edu/live/rss/events"

# def checkGrinnellTerms(body):
#     body = body.lower()
#     # TODO: Make editable in admin settings
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


#pylint: disable=C0301
#JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/near_location/8421/near_distance/10/paginate/false"
#JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/near_location/8421/near_distance/10"
JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all/paginate/"
# JSON_URL = "https://events.grinnell.edu/live/json/events/response_fields/all"


def scrapeCalendar(num_events = "false"):
    """ Scrapes Grinnell's events JSON feed """
    url =JSON_URL + str(num_events)
    events = json.loads(get(url, timeout=20).text)['data']

    # tags = []
    # TODO: Collect all possible tags

    for event in events: # TODO: Add filtering for intended audience (at least make sure it's not profs)
                         # And by location. And add tags for student orgs
        title = event['title']
        startTime = datetime.datetime.strptime(event['date_utc'], "%Y-%m-%d %H:%M:%S")
        startTime = pytz.utc.localize(startTime)
        if event['date2_utc']:
            endTime = datetime.datetime.strptime(event['date2_utc'], "%Y-%m-%d %H:%M:%S")
            endTime = pytz.utc.localize(endTime)
        else:
            endTime = startTime.astimezone(CST).replace(hour=23, minute=59).astimezone(pytz.utc)

        if event['location_title']:
            location = event['location_title']
        else:
            location = event['location']

        if event['description']: # TODO: Parse HTML
            description = event['description'].replace("<p>","").replace("</p>","").replace("\n","").strip()
        else:
            description = "" #pylint: disable=C0103

        externalID = event['id']

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
        
        # tags = str(tags).replace('[','').replace(']','').replace("'",'')

        if not location:
            continue

        # print(f"{event['title']} is taking place at {location} at "
        #     f"{startTime.astimezone(CST).strftime('%H:%M')}-{endTime.astimezone(CST).strftime('%H:%M')}")


        try:
            event = Event.objects.get(liveWhaleID = externalID)
            if event.host != autoPopulateUser: # We want to avoid changing them if someone has claimed it
                 continue
        except ObjectDoesNotExist:
            event = Event.objects.create(host = autoPopulateUser, title = title,
                                    location = location, start = startTime, end = endTime,
                                    description = description, studentsOnly = False, # I'm going to assume thats
                                        # if it was on the college's public calendar, we don't need to hide it
                                        # but also I know not all are, so maybe find a clever way to do this
                                    liveWhaleID = externalID)
        event.tags.clear()
        for tag in tags:
            if 'sport' in tag:
                tag = 'Sports'
            tag = tag.replace('amp;','')
            tag = string.capwords(tag)
            tagObj, created = Tag.objects.get_or_create(name=tag)
            event.tags.add(tagObj)
        event.save()



# TODO: Tabling tags

## This is what allows us to run this as a command from the console. The command name is the filename
class Command(BaseCommand):
    """ The wraper to run this command from the terminal """
    help = "Scrapes Grinnell's events calendar and adds them to GrinSync's database"

    # def add_arguments(self, parser):
        # TODO: Add overwrite, and potentally others
        #parser.add_argument("poll_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        scrapeCalendar(20)
