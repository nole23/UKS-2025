from unittest import TestCase
from unittest.mock import Mock, patch
from repository.signals import update_stars_count, update_pulls_count
from star.models import Star
from pull.models import Pull

class SignalTests(TestCase):

    def test_update_stars_count_post_save(self):
        # Mock repository i stars count
        mock_repo = Mock()
        mock_repo.stars.count.return_value = 5  # simuliramo 5 zvezdica
        mock_star = Mock(repository=mock_repo)

        # Poziv funkcije kao da je signal
        update_stars_count(sender=Star, instance=mock_star)

        # Provera da je stars_count postavljen i da je save pozvan
        mock_repo.stars.count.assert_called_once()
        mock_repo.save.assert_called_once_with(update_fields=['stars_count'])
        self.assertEqual(mock_repo.stars_count, 5)

    def test_update_stars_count_post_delete(self):
        # Isto kao post_save, signal je isti za post_delete
        mock_repo = Mock()
        mock_repo.stars.count.return_value = 2
        mock_star = Mock(repository=mock_repo)

        update_stars_count(sender=Star, instance=mock_star)

        mock_repo.stars.count.assert_called_once()
        mock_repo.save.assert_called_once_with(update_fields=['stars_count'])
        self.assertEqual(mock_repo.stars_count, 2)

    def test_update_pulls_count_post_save(self):
        # Mock repository i pulls count
        mock_repo = Mock()
        mock_repo.pulls.count.return_value = 3
        mock_pull = Mock(repository=mock_repo)

        update_pulls_count(sender=Pull, instance=mock_pull)

        mock_repo.pulls.count.assert_called_once()
        mock_repo.save.assert_called_once_with(update_fields=['pulls_count'])
        self.assertEqual(mock_repo.pulls_count, 3)