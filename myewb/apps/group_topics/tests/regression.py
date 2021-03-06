from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from base_groups.models import BaseGroup
from networks.models import Network
from group_topics.models import GroupTopic


class CreateTopics(TestCase):
    """
    Regression tests for
    https://cotonou.ewb.ca/fastrac/myewb2/ticket/389.
    """

    def setUp(self):
        self.top_user = User.objects.create_user('super', 'super@ewb.ca')
        self.base_group = BaseGroup.objects.create(slug='bg', creator=self.top_user)

    def tearDown(self):
        BaseGroup.objects.all().delete()
        User.objects.all().delete()

    def test_create_group_topic(self):
        gt = GroupTopic.objects.create(
                title="test",
                body="some test text.",
                group=self.base_group,
                creator=self.top_user)
        # make sure we create a topic
        self.assertTrue(gt)


class DeleteTopics(TestCase):
    """
    Regression tests for
    https://cotonou.ewb.ca/fastrac/myewb2/ticket/388.
    """

    def setUp(self):
        top_user = User.objects.create_user('super', 'super@ewb.ca')
        self.base_group = BaseGroup.objects.create(slug='bg', creator=top_user)

    def tearDown(self):
        BaseGroup.objects.all().delete()
        User.objects.all().delete()

    def test_topic_owner_can_delete(self):
        """
        The owner of a post should be able to delete it.
        """
        post_owner = User.objects.create_user(
                'owner',
                'owner@ewb.ca',
                'password')
        gt = GroupTopic.objects.create(
                creator=post_owner,
                group=self.base_group,
                title='test',
                body='words')
        topic_id = gt.id
        self.client.login(username='owner', password='password')
        response = self.client.post(
                reverse('topic_delete', kwargs={'topic_id': topic_id}),
                {'next': '/'})

        # make sure we get a redirect
        self.assertEquals(response.status_code, 302)
        # make sure the topic is deleted
        self.assertRaises(
                GroupTopic.DoesNotExist,
                GroupTopic.objects.get, id=topic_id)

    def test_other_user_cannot_delete(self):
        """
        A non-owner should not be able to delete a post.
        """
        post_owner = User.objects.create_user(
                'owner',
                'owner@ewb.ca',
                'password')
        gt = GroupTopic.objects.create(
                creator=post_owner,
                group=self.base_group,
                title='test',
                body='words')
        topic_id = gt.id
        other_user = User.objects.create_user(
                'other',
                'test.@ewb.ca',
                'password')
        self.client.login(username='other', password='password')
        response = self.client.post(
                reverse('topic_delete', kwargs={'topic_id': topic_id}),
                {'next': '/'})

        # make sure we get a redirect
        self.assertEquals(response.status_code, 302)
        # make sure the topic is still there
        self.assertEquals(gt, GroupTopic.objects.get(id=topic_id))

class TestPostToNowhere(TestCase):

    def setUp(self):
        self.creator = User.objects.create_user('creator', 'creator@ewb.ca', 'password')
        self.u = User.objects.create_user('tester', 'test@ewb.ca', 'password')

    def tearDown(self):
        GroupTopic.objects.all().delete()
        self.u.delete()
        self.creator.delete()

    def test_post_to_nowhere(self):
        c = self.client
        c.login(username='tester', password='password')
        post_count = GroupTopic.objects.all().count()
        c.post('/posts/', {'title': 'a post with no parent', 'body': 'some text'})
        self.assertEquals(post_count, GroupTopic.objects.all().count())

    def test_unauthorized_post_to_group(self):
        network = Network.objects.create(creator=self.creator, slug='net', visibility='M')
        c = self.client
        c.login(username='tester', password='password')
        post_count = GroupTopic.objects.all().count()
        c.post('/networks/net/posts/', {'title': 'a post with no parent', 'body': 'some text'})
        self.assertEquals(post_count, GroupTopic.objects.all().count())

class DanglingTags(TestCase):
    """
    Regression tests for
    https://office.ewb.ca/fastrac/myewb2/ticket/395
    """

    def setUp(self):
        # if we decide to truncate over 600 chars, increase this test string!!
        self.topic = GroupTopic(body="<div>this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends... this is the div that never ends... yes it goes on and on my friends...  </div>")

    def test_dangling_tags(self):
        self.assertEquals(self.topic.intro()[-9:], "</div>...")
        