from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from user.models import User
from .models import UserComment, UserFollow, UserPost, UserPostLike
from .views import DeleteCommentView, LikePostView, PostListView, PublishCommentView


class CommunityRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(username='作者', account_id='owner')
        cls.visitor = User.objects.create(username='访客', account_id='visitor')
        cls.public = UserPost.objects.create(user=cls.owner, content='公开')
        cls.private = UserPost.objects.create(user=cls.owner, content='私密', is_public=False)

    def setUp(self):
        self.factory = APIRequestFactory()
        signer = patch('comment.views.sign_oss_url', return_value='')
        signer.start()
        self.addCleanup(signer.stop)

    def call(self, view, viewer, method='post', **data):
        request = getattr(self.factory, method)('/', data, format='json')
        with patch('comment.views.get_current_user', return_value=viewer):
            return view.as_view()(request).data

    def posts(self, viewer, **params):
        response = self.call(PostListView, viewer, 'get', **params)
        self.assertEqual(response['code'], 0)
        return response['data']

    def comment(self, parent=None, post=None, user=None):
        return UserComment.objects.create(
            post=post or self.public, user=user or self.owner, content='评论',
            comment_parent=parent,
            comment_root=(parent.comment_root or parent) if parent else None,
            reply_to=parent.user if parent else None,
        )

    def assert_visible_comments(self, expected):
        post = next(post for post in self.posts(self.owner) if post['postId'] == self.public.id)
        ids = []
        for root in post['realComments']:
            self.assertIsNone(root['root_id'])
            self.assertEqual(root['child_count'], len(root['child_comments']))
            ids.append(root['id'])
            for child in root['child_comments']:
                self.assertEqual(child['root_id'], root['id'])
                ids.append(child['id'])
        self.assertEqual(post['comments'], len(expected))
        self.assertCountEqual(ids, [comment.id for comment in expected])

    def test_owner_sees_private_posts_with_self_or_numeric_id(self):
        for user_id in ('self', str(self.owner.id)):
            with self.subTest(user_id=user_id):
                self.assertCountEqual(
                    [post['postId'] for post in self.posts(self.owner, userId=user_id)],
                    [self.public.id, self.private.id],
                )

    def test_feeds_and_other_profiles_only_show_public_posts(self):
        UserFollow.objects.create(user=self.visitor, followed_user=self.owner)
        for viewer, params in (
            (self.owner, {}), (self.owner, {'type': 0}),
            (self.visitor, {'type': 2}), (None, {}),
            (self.visitor, {'userId': self.owner.id}), (None, {'userId': self.owner.id}),
        ):
            with self.subTest(viewer=viewer, params=params):
                self.assertEqual([post['postId'] for post in self.posts(viewer, **params)], [self.public.id])

    def test_private_posts_reject_other_users_reads_likes_and_comments(self):
        for viewer in (self.visitor, None):
            for view, method, params in (
                (LikePostView, 'get', {'postId': self.private.id}),
                (LikePostView, 'post', {'postId': self.private.id, 'isLiked': True}),
                (PublishCommentView, 'post', {'post_id': self.private.id, 'content': '越权'}),
            ):
                with self.subTest(viewer=viewer, view=view, method=method):
                    self.assertNotEqual(self.call(view, viewer, method, **params)['code'], 0)
        self.assertFalse(UserPostLike.objects.exists())
        self.assertFalse(UserComment.objects.exists())
        self.private.refresh_from_db()
        self.assertEqual(self.private.likes_count, 0)

    def test_public_interactions_and_owners_private_interactions_still_work(self):
        for post, viewer in ((self.public, self.visitor), (self.private, self.owner)):
            with self.subTest(post=post):
                for liked, expected_count in ((True, 1), (True, 1), (False, 0), (False, 0)):
                    response = self.call(LikePostView, viewer, postId=post.id, isLiked=liked)
                    self.assertEqual(response['code'], 0)
                    self.assertEqual(response['data'], {'isLiked': liked, 'likesCount': expected_count})
                self.assertEqual(self.call(LikePostView, viewer, 'get', postId=post.id)['code'], 0)
                self.assertEqual(self.call(PublishCommentView, viewer, post_id=post.id, content='正常评论')['code'], 0)

    def test_reply_parent_must_belong_to_the_same_post(self):
        parent = self.comment(post=self.private)
        response = self.call(PublishCommentView, self.visitor, post_id=self.public.id,
                             content='跨帖回复', parent_id=parent.id)
        self.assertNotEqual(response['code'], 0)
        self.assertEqual(UserComment.objects.count(), 1)

    def test_reply_rejects_forged_root_or_recipient(self):
        root = self.comment()
        child = self.comment(root)
        other_root = self.comment()
        foreign_root = self.comment(post=self.private)
        for extra in ({'root_id': other_root.id}, {'root_id': foreign_root.id},
                      {'reply_to_id': self.visitor.id}):
            with self.subTest(extra=extra):
                response = self.call(PublishCommentView, self.visitor, post_id=self.public.id,
                                     content='伪造关联', parent_id=child.id, **extra)
                self.assertNotEqual(response['code'], 0)
        self.assertEqual(UserComment.objects.count(), 4)

    def test_root_comment_rejects_reply_fields_without_parent(self):
        root = self.comment()
        for extra in ({'root_id': root.id}, {'reply_to_id': self.owner.id}):
            with self.subTest(extra=extra):
                response = self.call(PublishCommentView, self.visitor, post_id=self.public.id,
                                     content='缺少父评论', **extra)
                self.assertNotEqual(response['code'], 0)
        self.assertEqual(UserComment.objects.count(), 1)

    def test_normal_nested_reply_derives_root_and_recipient_from_parent(self):
        root = self.comment()
        child = self.comment(root, user=self.visitor)
        for parent in (root, child):
            for extra in ({}, {'root_id': str(root.id), 'reply_to_id': str(parent.user_id)}):
                with self.subTest(parent=parent, extra=extra):
                    response = self.call(PublishCommentView, self.owner, post_id=self.public.id,
                                         content='正常回复', parent_id=str(parent.id), **extra)
                    self.assertEqual(response['code'], 0)
                    reply = UserComment.objects.get(id=response['data']['id'])
                    self.assertEqual(reply.comment_parent, parent)
                    self.assertEqual(reply.comment_root, root)
                    self.assertEqual(reply.reply_to_id, parent.user_id)

    def test_all_replies_are_returned_for_frontend_expansion(self):
        root = self.comment()
        replies = [self.comment(root) for _ in range(7)]
        self.assert_visible_comments([root, *replies])

    def test_deleting_root_preserves_all_branches_and_reply_recipients(self):
        root = self.comment()
        child = self.comment(root, user=self.visitor)
        grandchild = self.comment(child)
        sibling = self.comment(root)
        cousin = self.comment(sibling, user=self.visitor)
        unrelated = self.comment()
        response = self.call(DeleteCommentView, self.owner, commentId=root.id)
        self.assertEqual(response['code'], 0)
        self.assert_visible_comments([child, grandchild, sibling, cousin, unrelated])
        child.refresh_from_db()
        self.assertIsNone(child.comment_parent_id)
        self.assertIsNone(child.comment_root_id)
        self.assertEqual(child.reply_to_id, self.owner.id)
        for reply in (grandchild, sibling, cousin):
            reply.refresh_from_db()
            self.assertEqual(reply.comment_root_id, child.id)
        self.assertEqual(grandchild.reply_to_id, self.visitor.id)
        self.assertEqual(sibling.reply_to_id, self.owner.id)
        self.assertEqual(cousin.comment_parent_id, sibling.id)
        # 新根评论仍可被正常回复。
        response = self.call(PublishCommentView, self.owner, post_id=self.public.id,
                             content='继续讨论', parent_id=grandchild.id, root_id=child.id,
                             reply_to_id=grandchild.user_id)
        self.assertEqual(response['code'], 0)

    def test_deleting_middle_comment_reparents_children_without_duplicates(self):
        root = self.comment()
        middle = self.comment(root, user=self.visitor)
        child = self.comment(middle)
        grandchild = self.comment(child)
        response = self.call(DeleteCommentView, self.visitor, commentId=middle.id)
        self.assertEqual(response['code'], 0)
        self.assert_visible_comments([root, child, grandchild])
        child.refresh_from_db()
        self.assertEqual(child.comment_parent_id, root.id)
        self.assertEqual(child.reply_to_id, self.visitor.id)

    def test_deleting_leaf_and_standalone_comment_still_works(self):
        root = self.comment()
        leaf = self.comment(root)
        for comment, remaining in ((leaf, [root]), (root, [])):
            response = self.call(DeleteCommentView, self.owner, commentId=comment.id)
            self.assertEqual(response['code'], 0)
            self.assert_visible_comments(remaining)

    def test_cannot_delete_another_users_comment(self):
        root = self.comment()
        child = self.comment(root)
        response = self.call(DeleteCommentView, self.visitor, commentId=root.id)
        self.assertNotEqual(response['code'], 0)
        self.assert_visible_comments([root, child])

    def test_failed_delete_rolls_back_reply_reparenting(self):
        root = self.comment()
        child = self.comment(root)
        with patch.object(UserComment, 'delete', side_effect=RuntimeError('test rollback')):
            response = self.call(DeleteCommentView, self.owner, commentId=root.id)
        self.assertNotEqual(response['code'], 0)
        child.refresh_from_db()
        self.assertEqual(child.comment_root_id, root.id)
        self.assertEqual(child.comment_parent_id, root.id)
        self.assert_visible_comments([root, child])
