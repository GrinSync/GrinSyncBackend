from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from api.models import User, Event

class PostTestCase(TestCase):
    def setUp(self):
        self.time = timezone.now()
        self.user1 = User.objects.create_user(username="admin", type = 'STU')
        Event.objects.create(host=self.user1,
                             name="Testing Event",
                            start=self.time,
                            end=self.time + timedelta(hours=1),
                            studentsOnly=True)

    def testEventIsPosted(self):
        """Posts are created"""
        test = Event.objects.get(host=self.user1)
        self.assertEqual(test.name, "Testing Event")

    # TODO: We'll add API test later
    # def test_valid_form_data(self):
    #     form = PostForm({
    #         'title': "Just testing",
    #         'text': "Repeated tests make the app foul-proof",
    #     })
    #     self.assertTrue(form.is_valid())
    #     post1 = form.save(commit=False)
    #     post1.author = self.user1
    #     post1.save()
    #     self.assertEqual(post1.title, "Just testing")
    #     self.assertEqual(post1.text, "Repeated tests make the app foul-proof")

    # def test_blank_form_data(self):
    #     form = PostForm({})
    #     self.assertFalse(form.is_valid())
    #     self.assertEqual(form.errors, {
    #         'title': ['This field is required.'],
    #         'text': ['This field is required.'],
    #     })