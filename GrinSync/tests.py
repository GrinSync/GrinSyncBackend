from datetime import timedelta
import json
import time
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework.authtoken import views as tokenViews
from rest_framework.test import force_authenticate
import api.views as views
from api.models import User, Event, Tag

# Django REST framework extends the standard RequestFactory to support API calls
factory = APIRequestFactory()
class APITestCase(TestCase):
    """ Tests for the backend API """
    def setUp(self):
        self.time = timezone.now()
        self.tag = Tag.objects.create(name = "Interesting Events", selectedDefault = True)
        print(Tag.objects.all()) # returns <QuerySet [<Tag: Tag object (1)>]>
        self.user1 = User.objects.create_user(username="admin", password="admintest", type = 'STU')
        print(self.user1.interestedTags.all()) # returns <QuerySet []>
        self.event1 = Event.objects.create(host=self.user1,
                            title="Testing Event",
                            start=self.time,
                            end=self.time + timedelta(hours=1),
                            studentsOnly=True)
        self.token1 = None
        self.user2 = User.objects.create_user(username="other", password="othertest", type = 'COM')
        self.event2 = Event.objects.create(host=self.user2,
                             title="Testing Event",
                            start=self.time,
                            end=self.time + timedelta(hours=1),
                            studentsOnly=False)
        self.token2 = None

    def testEventIsCreated(self):
        """ Test that events exist in the back end """
        test = Event.objects.get(host=self.user1)
        self.assertEqual(test.title, "Testing Event")

    def testLogin(self):
        """ Tests for login functionality """
        request = factory.post('/api/auth/', {'username': 'admin', 'password' : 'admintest'})
        response = tokenViews.obtain_auth_token(request).render()
        assert response.status_code == 200
        self.token1 = json.loads(response.content)['token']
        assert self.token1 is not None

        request = factory.post('/api/auth/', {'username': 'other', 'password' : 'othertest'})
        response = tokenViews.obtain_auth_token(request).render()
        assert response.status_code == 200
        self.token2 = json.loads(response.content)['token']
        assert self.token2 is not None

        request = factory.get('/api/validate/login')
        force_authenticate(request, user=self.user1, token=self.token1)
        response = views.validateLogin(request)
        assert response.status_code == 200  # This will be repeated to check if the requests were sucessful

    def testCanGetEvent(self):
        """ Tests that the events are accessible through the api """
        request = factory.get('/api/getEvent/', {'id': 1})
        force_authenticate(request, user=self.user1, token=self.token1)
        response = views.getEvent(request)
        assert response.status_code == 200
        self.assertNotEqual(json.loads(response.content), [])

    def testLikeEvent(self):
        """ Tests that we can like and unlike events """
        getRequest = factory.get('/api/getEvent/', {'id': 1})
        force_authenticate(getRequest, user=self.user1, token=self.token1)
        response = views.getEvent(getRequest)
        assert response.status_code == 200
        assert json.loads(response.content)['isFavorited'] is False

        likeRequest = factory.post('/api/toggleLikedEvent/', {'id': 1})
        force_authenticate(likeRequest, user=self.user1, token=self.token1)
        response = views.toggleLikedEvent(likeRequest)
        assert response.status_code == 200
        response = views.getEvent(getRequest)
        assert response.status_code == 200
        assert json.loads(response.content)['isFavorited'] is True

        response = views.toggleLikedEvent(likeRequest)
        assert response.status_code == 200
        response = views.getEvent(getRequest)
        assert response.status_code == 200
        assert json.loads(response.content)['isFavorited'] is False

    def testTags(self):
        """ Tests that events show up when tags are or aren't present """
        request = factory.get('/api/upcoming/')
        response = views.getUpcoming(request) #TODO: Update testing to include tags
        assert response.status_code == 200
        assert len(json.loads(response.content)) == 0 # None of the events have tags

        postRequest = factory.post('/api/upcoming/', {'id': self.event2.id, 'tag': "Interesting Events"})
        force_authenticate(postRequest, user=self.user2, token=self.token2)
        response = views.editEvent(postRequest)
        assert response.status_code == 200
        request = factory.get('/api/upcoming/')
        response = views.getUpcoming(request)
        assert response.status_code == 200
        assert len(json.loads(response.content)) == 1 # There's now 1 event with default tags

        postRequest = factory.post('/api/upcoming/', {'id': self.event1.id, 'tag': "Interesting Events"})
        force_authenticate(postRequest, user=self.user1, token=self.token1)
        response = views.editEvent(postRequest)
        assert response.status_code == 200
        request = factory.get('/api/upcoming/')
        force_authenticate(request, user=self.user1, token=self.token1)
        response = views.getUpcoming(request)
        assert response.status_code == 200
        # assert len(json.loads(response.content)) == 2 # There's now 2 event with default tags when you're logged in
        ## TODO: FIX ^

    def testStudentsOnly(self):
        """ Tests that student only events are only visible to students """
        self.event1.tags.add(self.tag)
        self.event1.save()
        self.event2.tags.add(self.tag)
        self.event2.save()
        request = factory.get('/api/upcoming/', {'tag':'ALL'})
        response = views.getUpcoming(request)
        assert response.status_code == 200
        assert len(json.loads(response.content)) == 1 # There's only 1 non-student event

        request = factory.get('/api/upcoming/', {'tag':'ALL'})
        force_authenticate(request, user=self.user1, token=self.token1)
        response = views.getUpcoming(request)
        assert response.status_code == 200
        assert len(json.loads(response.content)) == 2 # But when logged in we should be able to see both

    def testEditEvent(self):
        """ Tests that we can edit our events but not others'  """
        postRequest = factory.post('/api/editEvent/', {'id': 1, 'title': 'New Title!'})
        force_authenticate(postRequest, user=self.user1, token=self.token1)
        response = views.editEvent(postRequest)
        assert response.status_code == 200  # Making sure that editing doesn't cause errors
        getRequest = factory.get('/api/getEvent/', {'id': 1})
        force_authenticate(getRequest, user=self.user1, token=self.token1)
        response = views.getEvent(getRequest)
        assert response.status_code == 200
        assert json.loads(response.content)['title'] == 'New Title!'  # And that the changes take effect

        postRequest = factory.post('/api/editEvent/', {'id': 2, 'title': 'New Title!'})
        force_authenticate(postRequest, user=self.user1, token=self.token1)
        response = views.editEvent(postRequest)
        assert response.status_code == 403 # We want to make sure us editing others' events is forbidden
        getRequest = factory.get('/api/getEvent/', {'id': 2})
        force_authenticate(getRequest, user=self.user1, token=self.token1)
        response = views.getEvent(getRequest)
        assert response.status_code == 200
        assert json.loads(response.content)['title'] != 'New Title!' # And that there's no effect
