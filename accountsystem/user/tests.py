from django.test import TestCase
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from .models import User
from .views import GetUserInfoView


class ProfilePrivacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create(mobile='19900000001', account_id='owner')
        cls.visitor = User.objects.create(mobile='19900000002', account_id='visitor')

    def profile(self, viewer, user_id):
        request = APIRequestFactory().get('/', {'userId': user_id})
        with patch('user.views.get_current_user', return_value=viewer), \
                patch('user.views.sign_oss_url', return_value=''):
            response = GetUserInfoView.as_view()(request).data
        self.assertEqual(response['code'], 0)
        return response['data']

    def test_self_keeps_mobile_and_existing_name_fallbacks(self):
        for user_id in ('self', str(self.owner.id)):
            with self.subTest(user_id=user_id):
                data = self.profile(self.owner, user_id)
                self.assertTrue(data['isSelf'])
                for field in ('mobile', 'username', 'nickname'):
                    self.assertEqual(data[field], self.owner.mobile)

    def test_other_and_anonymous_profiles_do_not_expose_mobile(self):
        for viewer in (self.visitor, None):
            with self.subTest(viewer=viewer):
                data = self.profile(viewer, self.owner.id)
                self.assertFalse(data['isSelf'])
                self.assertIsNone(data['mobile'])
                self.assertTrue(data['username'])
                self.assertTrue(data['nickname'])
                self.assertNotIn(self.owner.mobile, str(data))

    def test_public_profile_keeps_explicit_names(self):
        self.owner.username = '姓名'
        self.owner.nickname = '昵称'
        self.owner.save()
        data = self.profile(self.visitor, self.owner.id)
        self.assertEqual(data['username'], '姓名')
        self.assertEqual(data['nickname'], '昵称')
