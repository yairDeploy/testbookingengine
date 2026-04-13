from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta, datetime, time
from unittest.mock import patch
from decimal import Decimal
from pms.models import Booking, Room, Room_type, Customer


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class DashboardViewTest(TestCase):
    """Unit tests for DashboardView"""
    
    def setUp(self):
        """Set up test data"""
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)
        
        
        self.room_type = Room_type.objects.create(
            name="Standard Room",
            price=100.00,
            max_guests=2
        )
        
        
        self.room1 = Room.objects.create(
            room_type=self.room_type,
            name="Room 101",
            description="Standard room with view"
        )
        
        self.room2 = Room.objects.create(
            room_type=self.room_type,
            name="Room 102",
            description="Standard room without view"
        )
        
        self.room3 = Room.objects.create(
            room_type=self.room_type,
            name="Room 103",
            description="Deluxe room"
        )
        
        
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        
        self.url = reverse('dashboard')
    
    def test_dashboard_view_returns_200(self):
        """Test that dashboard view returns 200 status code"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_view_uses_correct_template(self):
        """Test that dashboard view uses the correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "dashboard.html")
    
    def test_dashboard_context_contains_required_keys(self):
        """Test that dashboard context contains all required keys"""
        response = self.client.get(self.url)
        self.assertIn('dashboard', response.context)
        
        dashboard = response.context['dashboard']
        self.assertIn('new_bookings', dashboard)
        self.assertIn('incoming_guests', dashboard)
        self.assertIn('outcoming_guests', dashboard)
        self.assertIn('invoiced', dashboard)
        self.assertIn('occupancy_rate', dashboard)
    
    def test_new_bookings_count_for_today(self):
        """Test that new_bookings counts bookings created today"""
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="TODAY001"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.tomorrow + timedelta(days=1),
            checkout=self.tomorrow + timedelta(days=4),
            state=Booking.NEW,
            guests=1,
            customer=self.customer,
            total=300.00,
            code="TODAY002"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['new_bookings'], 2)
    
    def test_incoming_guests_count(self):
        """Test that incoming_guests counts bookings checking in today"""
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="INCOMING001"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.today,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=3,
            customer=self.customer,
            total=700.00,
            code="INCOMING002"
        )
        
        
        booking3 = Booking.objects.create(
            room=self.room3,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="FUTURE001"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['incoming_guests'], 2)
    
    def test_incoming_guests_excludes_deleted_bookings(self):
        """Test that incoming_guests excludes deleted/cancelled bookings"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.DELETED,  
            guests=2,
            customer=self.customer,
            total=100.00,
            code="DEL_INCOMING"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="ACTIVE_INCOMING"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        
        self.assertEqual(dashboard['incoming_guests'], 1)
    
    def test_outcoming_guests_count(self):
        """Test that outcoming_guests counts bookings checking out today"""
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.yesterday,
            checkout=self.today,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="OUTCOMING001"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.yesterday - timedelta(days=1),
            checkout=self.today,
            state=Booking.NEW,
            guests=4,
            customer=self.customer,
            total=200.00,
            code="OUTCOMING002"
        )
        
        
        booking3 = Booking.objects.create(
            room=self.room3,
            checkin=self.yesterday,
            checkout=self.tomorrow,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=150.00,
            code="FUTURE_OUT"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['outcoming_guests'], 2)
    
    def test_outcoming_guests_excludes_deleted_bookings(self):
        """Test that outcoming_guests excludes deleted/cancelled bookings"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.yesterday,
            checkout=self.today,
            state=Booking.DELETED,  
            guests=2,
            customer=self.customer,
            total=100.00,
            code="DEL_OUTCOMING"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.yesterday,
            checkout=self.today,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="ACTIVE_OUTCOMING"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        
        self.assertEqual(dashboard['outcoming_guests'], 1)
    
    def test_invoiced_sum_for_today(self):
        """Test that invoiced aggregates total for bookings created today"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=500.00,
            code="INVOICE001"
        )
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.tomorrow + timedelta(days=1),
            checkout=self.tomorrow + timedelta(days=3),
            state=Booking.NEW,
            guests=1,
            customer=self.customer,
            total=300.00,
            code="INVOICE002"
        )
        
        booking3 = Booking.objects.create(
            room=self.room3,
            checkin=self.tomorrow + timedelta(days=2),
            checkout=self.tomorrow + timedelta(days=5),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=200.00,
            code="INVOICE003"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        expected_total = Decimal('1000.00')
        self.assertEqual(dashboard['invoiced']['total__sum'], expected_total)
    
    def test_invoiced_excludes_deleted_bookings(self):
        """Test that invoiced excludes deleted/cancelled bookings"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.DELETED,
            guests=2,
            customer=self.customer,
            total=1000.00,
            code="DEL_INVOICE"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=500.00,
            code="ACTIVE_INVOICE"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        
        self.assertEqual(dashboard['invoiced']['total__sum'], Decimal('500.00'))
    
    def test_invoiced_returns_none_when_no_bookings(self):
        """Test that invoiced returns None when no bookings created today"""
        
        Booking.objects.all().delete()
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertIsNone(dashboard['invoiced']['total__sum'])
    
    def test_occupancy_rate_calculation(self):
        """Test that occupancy rate is calculated correctly"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="OCC001"
        )
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="OCC002"
        )
        
        
        
        
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        expected_rate = (2 / 3) * 100
        self.assertAlmostEqual(dashboard['occupancy_rate'], expected_rate, places=2)
    
    def test_occupancy_rate_with_no_rooms(self):
        """Test that occupancy rate is 0 when there are no rooms"""
        
        Room.objects.all().delete()
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['occupancy_rate'], 0)
    
    def test_occupancy_rate_with_no_confirmed_bookings(self):
        """Test that occupancy rate is 0 when there are no confirmed bookings"""
        
        Booking.objects.all().delete()
        
        
        booking = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.DELETED,  
            guests=2,
            customer=self.customer,
            total=700.00,
            code="DEL_OCC"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['occupancy_rate'], 0)
    
    def test_occupancy_rate_excludes_deleted_bookings(self):
        """Test that occupancy rate only counts NEW state bookings"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="NEW_OCC"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.DELETED,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="DEL_OCC"
        )
        
        
        
        
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        expected_rate = (1 / 3) * 100
        self.assertAlmostEqual(dashboard['occupancy_rate'], expected_rate, places=2)
    
    def test_all_metrics_together(self):
        """Test that all dashboard metrics work correctly together"""
        
        Booking.objects.all().delete()
        
        
        booking1 = Booking.objects.create(
            room=self.room1,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="ALL001"
        )
        
        
        booking2 = Booking.objects.create(
            room=self.room2,
            checkin=self.yesterday,
            checkout=self.today,
            state=Booking.NEW,
            guests=3,
            customer=self.customer,
            total=150.00,
            code="ALL002"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        
        self.assertEqual(dashboard['new_bookings'], 2)  
        self.assertEqual(dashboard['incoming_guests'], 1)  
        self.assertEqual(dashboard['outcoming_guests'], 1)  
        self.assertEqual(dashboard['invoiced']['total__sum'], Decimal('250.00'))  
        
        
        expected_rate = (2 / 3) * 100
        self.assertAlmostEqual(dashboard['occupancy_rate'], expected_rate, places=2)
    
    def test_dashboard_with_no_data(self):
        """Test dashboard behavior when there is no data at all"""
        
        Booking.objects.all().delete()
        Room.objects.all().delete()
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        self.assertEqual(dashboard['new_bookings'], 0)
        self.assertEqual(dashboard['incoming_guests'], 0)
        self.assertEqual(dashboard['outcoming_guests'], 0)
        self.assertIsNone(dashboard['invoiced']['total__sum'])
        self.assertEqual(dashboard['occupancy_rate'], 0)
    
    def test_dashboard_with_multiple_rooms_and_bookings(self):
        """Test dashboard with complex scenario of multiple rooms and bookings"""
        
        Booking.objects.all().delete()
        
        
        room4 = Room.objects.create(
            room_type=self.room_type,
            name="Room 104",
            description="Extra room"
        )
        
        room5 = Room.objects.create(
            room_type=self.room_type,
            name="Room 105",
            description="Another room"
        )
        
        
        
        Booking.objects.create(
            room=self.room1,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="SCENE001"
        )
        
        
        Booking.objects.create(
            room=self.room2,
            checkin=self.yesterday,
            checkout=self.today,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=100.00,
            code="SCENE002"
        )
        
        
        Booking.objects.create(
            room=self.room3,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=500.00,
            code="SCENE003"
        )
        
        
        Booking.objects.create(
            room=room4,
            checkin=self.today,
            checkout=self.tomorrow,
            state=Booking.DELETED,
            guests=2,
            customer=self.customer,
            total=1000.00,
            code="SCENE_DEL"
        )
        
        response = self.client.get(self.url)
        dashboard = response.context['dashboard']
        
        
        self.assertEqual(dashboard['new_bookings'], 4)
        
        self.assertEqual(dashboard['incoming_guests'], 1)
        
        self.assertEqual(dashboard['outcoming_guests'], 1)
        
        self.assertEqual(dashboard['invoiced']['total__sum'], Decimal('700.00'))
        
        self.assertEqual(dashboard['occupancy_rate'], 60.0)