"""
Tests for the Django Forum application.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from forum import auth
from forum.models import Forum, ForumProfile, Post, Section, Topic

class ForumProfileTestCase(TestCase):
    fixtures = ['testdata.json']

    def test_auth_methods(self):
        """
        Verifies authorisation-related instance methods.
        """
        profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(profile.is_admin(), True)
        self.assertEquals(profile.is_moderator(), True)

        profile = ForumProfile.objects.get(pk=2)
        self.assertEquals(profile.is_admin(), False)
        self.assertEquals(profile.is_moderator(), True)

        profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(profile.is_admin(), False)
        self.assertEquals(profile.is_moderator(), False)

class SectionTestCase(TestCase):
    """
    Tests for the Section model:

    - Delete a Section.
    """
    fixtures = ['testdata.json']

    def test_delete_section(self):
        """
        Verifies that deleting a Section has the appropriate effect on
        the ordering of existing Sections and User postcounts.
        """
        section = Section.objects.get(pk=1)
        section.delete()

        self.assertEquals(Section.objects.get(pk=2).order, 1)
        self.assertEquals(Section.objects.get(pk=3).order, 2)

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 36)
            self.assertEquals(forum_profile.post_count, 36)

class ForumTestCase(TestCase):
    """
    Tests for the Forum model:

    - Delete a Forum.
    """
    fixtures = ['testdata.json']

    def test_delete_forum(self):
        """
        Verifies that deleting a Forum has the appropriate effect on
        the ordering of existing Forums and User postcounts.
        """
        forum = Forum.objects.get(pk=1)
        forum.delete()

        self.assertEquals(Forum.objects.get(pk=2).order, 1)
        self.assertEquals(Forum.objects.get(pk=3).order, 2)

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 48)
            self.assertEquals(forum_profile.post_count, 48)

class TopicTestCase(TestCase):
    """
    Tests for the Topic model:

    - Add a Topic
    - Edit a Topic
    - Delete a Topic

    The following tests are for appropriate changes to denormalised
    data:

    - Edit the last Topic in a Forum
    - Delete the last Topic in a Forum
    """
    fixtures = ['testdata.json']

    def test_add_topic(self):
        """
        Verifies that adding a Topic (and its opening Post) has the
        appropriate effect on denormalised data.
        """
        user = User.objects.get(pk=1)
        forum = Forum.objects.get(pk=1)
        topic = Topic.objects.create(forum=forum, user=user, title='Test Topic')

        post = Post.objects.create(topic=topic, user=user, body='Test Post.')
        self.assertEquals(post.num_in_topic, 1)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=topic.id)
        self.assertEquals(topic.posts.count(), 1)
        self.assertEquals(topic.post_count, 1)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 4)
        self.assertEquals(forum.topic_count, 4)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 55)
        self.assertEquals(forum_profile.post_count, 55)

    def test_edit_topic(self):
        """
        Verifies that editing the title of a Topic which does *not*
        contain the last Post in its Forum does not affect anything but
        the Topic.
        """
        topic = Topic.objects.get(pk=1)
        topic.title = 'Updated Title'
        topic.save()

        last_post = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, last_post.topic.id)
        self.assertEquals(forum.last_topic_title, last_post.topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_topic(self):
        """
        Verifies that deleting a Topic has the appropriate effect on
        denormalised data.
        """
        Topic.objects.get(pk=1).delete()

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)

        user = User.objects.get(pk=1)
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 48)
        self.assertEquals(forum_profile.post_count, 48)

    def test_edit_last_topic(self):
        """
        Verifies that editing the title of the Topic which contains the
        last post in a Forum results in the Forum's denormalised data
        being updated appropriately.
        """
        topic = Topic.objects.get(pk=3)
        topic.title = 'Updated Title'
        topic.save()

        last_post = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_last_post_topic(self):
        """
        Verifies that deleting the Topic which contains the last Post
        in a Forum results in the forum's denormalised last post data
        being updated appropriately.
        """
        topic = Topic.objects.get(pk=3)
        topic.delete()

        last_post = Post.objects.get(pk=6)
        last_topic = Topic.objects.get(pk=2)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 2)
        self.assertEquals(forum.topic_count, 2)
        self.assertEquals(forum.last_post_at, last_post.posted_at)
        self.assertEquals(forum.last_topic_id, last_topic.id)
        self.assertEquals(forum.last_topic_title, last_topic.title)
        self.assertEquals(forum.last_user_id, last_post.user.id)
        self.assertEquals(forum.last_username, last_post.user.username)

    def test_delete_last_topic(self):
        """
        Verifies that deleting the last Topic in a Forum results in the
        forum's denormalised last Post data being cleared.
        """
        topics = Topic.objects.filter(pk__in=[1,2,3])
        for topic in topics:
            topic.delete()

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 0)
        self.assertEquals(forum.topic_count, 0)
        self.assertEquals(forum.last_post_at, None)
        self.assertEquals(forum.last_topic_id, None)
        self.assertEquals(forum.last_topic_title, '')
        self.assertEquals(forum.last_user_id, None)
        self.assertEquals(forum.last_username, '')

        users = User.objects.filter(pk__in=[1,2,3])
        for user in users:
            forum_profile = ForumProfile.objects.get_for_user(user)
            self.assertEquals(user.posts.count(), 48)
            self.assertEquals(forum_profile.post_count, 48)

class PostTestCase(TestCase):
    """
    Tests for the Post model:

    - Add a Post
    - Edit a Post
    - Delete a Post

    The following tests are for appropriate changes to denormalised
    data:

    - Delete the last Post in a Topic
    - Delete the last Post in a Forum
    """
    fixtures = ['testdata.json']

    def test_add_post(self):
        """
        Verifies that adding a Post to a Topic has the appropriate
        effect on denormalised data.
        """
        user = User.objects.get(pk=1)
        topic = Topic.objects.get(pk=1)

        post = Post.objects.create(topic=topic, user=user, body='Test Post.')
        self.assertEquals(post.num_in_topic, 4)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.body_html, '')
        self.assertEquals(post.edited_at, None)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 7)
        self.assertEquals(topic.post_count, 4)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 55)
        self.assertEquals(forum_profile.post_count, 55)

    def test_edit_post(self):
        """
        Verifies that editing a Post results in appropriate Post fields
        being updated and doesn't have any effect on denormalised data.
        """
        post = Post.objects.get(pk=9)
        post.body = 'Test Post.'
        post.save()
        self.assertEquals(post.num_in_topic, 3)
        self.assertNotEquals(post.posted_at, None)
        self.assertNotEquals(post.edited_at, None)
        self.assertTrue(post.edited_at > post.posted_at)
        self.assertNotEquals(post.body_html, '')

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.posts.count(), 6)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.post_count, 3)
        self.assertEquals(topic.last_post_at, post.posted_at)
        self.assertEquals(topic.last_user_id, post.user_id)
        self.assertEquals(topic.last_username, post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, post.user_id)
        self.assertEquals(forum.last_username, post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(user.posts.count(), 54)
        self.assertEquals(forum_profile.post_count, 54)

    def test_delete_post(self):
        """
        Verifies that deleting a Post which is *not* the last Post in
        its topic results in following Posts' position counters being
        decremented appropriately, and that last Post denormalised data
        is unaffected.
        """
        post = Post.objects.get(pk=1)
        post.delete()

        self.assertEquals(Post.objects.get(pk=2).num_in_topic, 1)
        last_post = Post.objects.get(pk=3)
        self.assertEquals(last_post.num_in_topic, 2)

        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, last_post.posted_at)
        self.assertEquals(topic.last_user_id, last_post.user_id)
        self.assertEquals(topic.last_username, last_post.user.username)

        user = post.user
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

    def test_delete_last_post_in_topic(self):
        """
        Verifies that deleting the last Post in a Topic has the
        appropriate effect on its denormalised data.
        """
        post = Post.objects.get(pk=3)
        post.delete()

        previous_post_in_topic = Post.objects.get(pk=2)
        topic = Topic.objects.get(pk=1)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, previous_post_in_topic.posted_at)
        self.assertEquals(topic.last_user_id, previous_post_in_topic.user_id)
        self.assertEquals(topic.last_username, previous_post_in_topic.user.username)

        last_post_in_forum = Post.objects.get(pk=9)
        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, last_post_in_forum.posted_at)
        self.assertEquals(forum.last_topic_id, last_post_in_forum.topic.id)
        self.assertEquals(forum.last_topic_title, last_post_in_forum.topic.title)
        self.assertEquals(forum.last_user_id, last_post_in_forum.user_id)
        self.assertEquals(forum.last_username, last_post_in_forum.user.username)

        user = User.objects.get(pk=1)
        forum_profile = ForumProfile.objects.get(pk=1)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

    def test_delete_last_post_in_forum(self):
        """
        Verifies that deleting the last Post in a Forum has the
        appropriate effect on denormalised data, including Forum and
        Topic last post data being reset appropriately.
        """
        post = Post.objects.get(pk=9)
        post.delete()

        previous_post = Post.objects.get(pk=8)

        topic = Topic.objects.get(pk=3)
        self.assertEquals(topic.posts.count(), 5)
        self.assertEquals(topic.post_count, 2)
        self.assertEquals(topic.metapost_count, 3)
        self.assertEquals(topic.last_post_at, previous_post.posted_at)
        self.assertEquals(topic.last_user_id, previous_post.user_id)
        self.assertEquals(topic.last_username, previous_post.user.username)

        forum = Forum.objects.get(pk=1)
        self.assertEquals(forum.topics.count(), 3)
        self.assertEquals(forum.topic_count, 3)
        self.assertEquals(forum.last_post_at, previous_post.posted_at)
        self.assertEquals(forum.last_topic_id, topic.id)
        self.assertEquals(forum.last_topic_title, topic.title)
        self.assertEquals(forum.last_user_id, previous_post.user_id)
        self.assertEquals(forum.last_username, previous_post.user.username)

        user = User.objects.get(pk=3)
        forum_profile = ForumProfile.objects.get(pk=3)
        self.assertEquals(user.posts.count(), 53)
        self.assertEquals(forum_profile.post_count, 53)

class ManagerTestCase(TestCase):
    """
    Tests for custom Manager methods which add extra data to retrieved
    objects.
    """
    fixtures = ['testdata.json']

    def test_post_manager_with_user_details(self):
        post = Post.objects.with_user_details().get(pk=1)
        forum_profile = ForumProfile.objects.get_for_user(post.user)
        self.assertEquals(post.user_username, post.user.username)
        self.assertEquals(post.user_date_joined, post.user.date_joined)
        self.assertEquals(post.user_title, forum_profile.title)
        self.assertEquals(post.user_avatar, forum_profile.avatar)
        self.assertEquals(post.user_post_count, forum_profile.post_count)
        self.assertEquals(post.user_location, forum_profile.location)
        self.assertEquals(post.user_website, forum_profile.website)

    def test_topic_manager_with_user_details(self):
        topic = Topic.objects.with_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)

    def test_topic_manager_with_forum_details(self):
        topic = Topic.objects.with_forum_details().get(pk=1)
        self.assertEquals(topic.forum_name, topic.forum.name)

    def test_topic_manager_with_forum_and_user_details(self):
        topic = Topic.objects.with_forum_and_user_details().get(pk=1)
        self.assertEquals(topic.user_username, topic.user.username)
        self.assertEquals(topic.forum_name, topic.forum.name)

class AuthTestCase(TestCase):
    """
    Tests for the authorisation module.
    """
    fixtures = ['testdata.json']

    def setUp(self):
        """
        Retrieves a user from each user group for convenience.
        """
        self.admin = User.objects.get(pk=1)
        self.moderator = User.objects.get(pk=2)
        self.user = User.objects.get(pk=3)

    def test_is_admin(self):
        """
        Verifies the check for a user having Administrator privileges.
        """
        self.assertTrue(auth.is_admin(self.admin))
        self.assertFalse(auth.is_admin(self.moderator))
        self.assertFalse(auth.is_admin(self.user))

    def test_is_moderator(self):
        """
        Verifies the check for a user having Moderator privileges.
        """
        self.assertTrue(auth.is_moderator(self.admin))
        self.assertTrue(auth.is_moderator(self.moderator))
        self.assertFalse(auth.is_moderator(self.user))

    def test_user_can_edit_post(self):
        """
        Verifies the check for a given user being able to edit a given
        Post.

        Members of the User group may only edit their own Posts if they
        are not in unlocked Topics.
        """
        # Post by admin
        post = Post.objects.get(pk=1)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertFalse(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

        # Post by moderator
        post = Post.objects.get(pk=4)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertFalse(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

        # Post by user
        post = Post.objects.get(pk=7)
        topic = post.topic
        self.assertTrue(auth.user_can_edit_post(self.admin, post))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post))
        self.assertTrue(auth.user_can_edit_post(self.user, post))
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.user, post, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_post(self.admin, post, topic))
        self.assertTrue(auth.user_can_edit_post(self.moderator, post, topic))
        self.assertFalse(auth.user_can_edit_post(self.user, post, topic))

    def test_user_can_edit_topic(self):
        """
        Verifies the check for a given user being able to edit a given
        Topic.

        Members of the User group may only edit their own Topics if they
        are not locked.
        """
        # Topic creeated by admin
        topic = Topic.objects.get(pk=1)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

        # Topic created by moderator
        topic = Topic.objects.get(pk=2)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

        # Topic created by user
        topic = Topic.objects.get(pk=3)
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertTrue(auth.user_can_edit_topic(self.user, topic))
        topic.locked = True
        self.assertTrue(auth.user_can_edit_topic(self.admin, topic))
        self.assertTrue(auth.user_can_edit_topic(self.moderator, topic))
        self.assertFalse(auth.user_can_edit_topic(self.user, topic))

    def test_user_can_edit_user_profile(self):
        """
        Verifies the check for a given user being able to edit another
        given user's public ForumProfile.

        Members of the User group may only edit their own ForumProfile.
        """
        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.admin))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.admin))
        self.assertFalse(auth.user_can_edit_user_profile(self.user, self.admin))

        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.moderator))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.moderator))
        self.assertFalse(auth.user_can_edit_user_profile(self.user, self.moderator))

        self.assertTrue(auth.user_can_edit_user_profile(self.admin, self.user))
        self.assertTrue(auth.user_can_edit_user_profile(self.moderator, self.user))
        self.assertTrue(auth.user_can_edit_user_profile(self.user, self.user))
