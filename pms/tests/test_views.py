from django.test import TestCase, Client
from django.urls import reverse
from datetime import datetime, timedelta
from pms.models import Room, Room_type, Booking
class RoomFilterViewTest(TestCase):
	def setUp(self):
		self.client = Client()
		self.room_type = Room_type.objects.create(name="Doble", price=100.0, max_guests=2)
		self.room = Room.objects.create(room_type=self.room_type, name="101", description="Vista al mar")
		self.url = reverse('room_filter')
	def test_post_returns_available_room(self):
		checkin = (datetime.today() + timedelta(days=1)).date()
		checkout = (datetime.today() + timedelta(days=2)).date()
		data = {
    			'checkin': checkin.strftime('%Y-%m-%d'),
			'checkout': checkout.strftime('%Y-%m-%d'),
			'guests': 2
		}
		response = self.client.post(self.url, data)
		self.assertEqual(response.status_code, 200)
		json_data = response.json()
		self.assertIn('rooms', json_data)
		self.assertEqual(len(json_data['rooms']), 1)
		self.assertEqual(json_data['rooms'][0]['name'], "101")
	def test_post_with_name_filter(self):
		checkin = (datetime.today() + timedelta(days=1)).date()
		checkout = (datetime.today() + timedelta(days=2)).date()
		data = {
    			'checkin': checkin.strftime('%Y-%m-%d'),
			'checkout': checkout.strftime('%Y-%m-%d'),
			'guests': 2,
			'name_filter': '101'
		}
		response = self.client.post(self.url, data)
		self.assertEqual(response.status_code, 200)
		json_data = response.json()
		self.assertEqual(len(json_data['rooms']), 1)
		self.assertEqual(json_data['rooms'][0]['name'], "101")
	def test_post_excludes_booked_room(self):
		checkin = (datetime.today() + timedelta(days=1)).date()
		checkout = (datetime.today() + timedelta(days=2)).date()
		# Crear una reserva que bloquea la habitación
		Booking.objects.create(
    			room=self.room,
			checkin=checkin,
			checkout=checkout,
			guests=2,
			customer=None,
			total=100.0,
			code="RES123",
			state="NEW"
		)
		data = {
    			'checkin': checkin.strftime('%Y-%m-%d'),
			'checkout': checkout.strftime('%Y-%m-%d'),
			'guests': 2
		}
		response = self.client.post(self.url, data)
		json_data = response.json()
		self.assertEqual(len(json_data['rooms']), 0)
	def test_post_json_format(self):
		checkin = (datetime.today() + timedelta(days=1)).date()
		checkout = (datetime.today() + timedelta(days=2)).date()
		data = {
    			'checkin': checkin.strftime('%Y-%m-%d'),
			'checkout': checkout.strftime('%Y-%m-%d'),
			'guests': 2
		}
		response = self.client.post(self.url, data)
		json_data = response.json()
		self.assertIn('rooms', json_data)
		self.assertIn('total_rooms', json_data)
		self.assertIn('total_days', json_data)
	def test_post_no_rooms_available(self):
		checkin = (datetime.today() + timedelta(days=1)).date()
		checkout = (datetime.today() + timedelta(days=2)).date()
		# Eliminar todas las habitaciones
		Room.objects.all().delete()
		data = {
    			'checkin': checkin.strftime('%Y-%m-%d'),
			'checkout': checkout.strftime('%Y-%m-%d'),
			'guests': 2
		}
		response = self.client.post(self.url, data)
		json_data = response.json()
		self.assertEqual(len(json_data['rooms']), 0)
