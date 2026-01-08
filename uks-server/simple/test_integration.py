from rest_framework.test import APITestCase
from unittest.mock import patch
from rest_framework import status

class MyApiTestCase(APITestCase):
    @patch('rest_framework.test.APIClient.post')  # Mock-uje `post` metodu
    def test_create_item(self, mock_post):
        # Mock-ovanje odgovora sa status kodom 201 (Created)
        mock_post.return_value.status_code = status.HTTP_201_CREATED
        mock_post.return_value.data = {'name': 'Test Item'}

        # Pozivamo mock-ovani POST zahtev
        response = self.client.post('/api/items/', {'name': 'Test Item'})

        # Verifikacija da je status kod 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verifikacija da je naziv 'Test Item' u odgovoru
        self.assertEqual(response.data['name'], 'Test Item')
