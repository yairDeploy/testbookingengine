from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from datetime import date, timedelta
from pms.models import Booking, Room, Room_type, Customer
from pms.views import UpdateBookingView


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UpdateBookingViewTest(TestCase):
    """Unit tests for UpdateBookingView"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.day_after_tomorrow = self.today + timedelta(days=2)
        self.next_week = self.today + timedelta(days=7)
        
    
        self.room_type = Room_type.objects.create(
            name="Standard Room",
            price=100.00,
            max_guests=2
        )
        
    
        self.room = Room.objects.create(
            room_type=self.room_type,
            name="Test Room 101",
            description="A comfortable test room"
        )
        
    
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890"
        )
        
    
        self.booking = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow,
            checkout=self.next_week,
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=700.00,
            code="TEST001"
        )
        
        self.url = reverse('update_booking', kwargs={'pk': self.booking.id})
    
    def test_get_request_renders_update_form(self):
        """Test that GET request renders the form with booking data"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "update_booking.html")
        self.assertIn('booking_form', response.context)
        self.assertIn('booking', response.context)
        self.assertEqual(response.context['booking'], self.booking)
        
    
        form = response.context['booking_form']
        self.assertEqual(form.prefix, "booking")
        self.assertEqual(form.instance, self.booking)
    
    def test_get_request_with_invalid_pk_returns_404(self):
        """Test that GET with invalid pk returns 404"""
        invalid_url = reverse('update_booking', kwargs={'pk': 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_post_valid_update_without_conflicts_redirects(self):
        """Test that POST with valid data without conflicts redirects to home"""
        post_data = {
            'booking-checkin': self.day_after_tomorrow.strftime('%Y-%m-%d'),
            'booking-checkout': (self.day_after_tomorrow + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
    
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        
    
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, self.day_after_tomorrow)
        self.assertEqual(self.booking.checkout, self.day_after_tomorrow + timedelta(days=3))
    
    def test_post_valid_update_updates_booking(self):
        """Test that POST correctly updates the booking"""
        new_checkin = self.tomorrow + timedelta(days=1)
        new_checkout = self.tomorrow + timedelta(days=5)
        
        post_data = {
            'booking-checkin': new_checkin.strftime('%Y-%m-%d'),
            'booking-checkout': new_checkout.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, new_checkin)
        self.assertEqual(self.booking.checkout, new_checkout)
    
    def test_post_with_conflicting_booking_shows_error(self):
        """Test that POST with conflicting dates shows error"""
    
        conflicting_booking = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow + timedelta(days=2),
            checkout=self.tomorrow + timedelta(days=4),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=200.00,
            code="CONF001"
        )
        
    
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=1)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
    
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "update_booking.html")
        
    
        form = response.context['booking_form']
        self.assertFalse(form.is_valid())
        self.assertIn('No hay disponibilidad para las fechas seleccionadas', str(form.non_field_errors()))
        
    
        self.booking.refresh_from_db()
        self.assertNotEqual(self.booking.checkin, self.tomorrow + timedelta(days=1))
    
    def test_post_with_conflicting_booking_excludes_current_booking(self):
        """Test that conflict check excludes the current booking"""
    
        other_booking = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow + timedelta(days=3),
            checkout=self.tomorrow + timedelta(days=5),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=200.00,
            code="OTHER001"
        )
        
    
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=1)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=2)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
    
        self.assertEqual(response.status_code, 302)
        
    
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, self.tomorrow + timedelta(days=1))
        self.assertEqual(self.booking.checkout, self.tomorrow + timedelta(days=2))
    
    def test_post_with_invalid_form_data_rerenders_form(self):
        """Test that POST with invalid data re-renders form with errors"""
        post_data = {
            'booking-checkin': 'invalid-date',
            'booking-checkout': 'invalid-date'
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "update_booking.html")
        
    
        form = response.context['booking_form']
        self.assertFalse(form.is_valid())
        self.assertIn('checkin', form.errors)
    
    def test_post_with_checkout_less_than_checkin_shows_error(self):
        """Test that POST with checkout earlier than checkin shows validation error"""
        post_data = {
            'booking-checkin': self.next_week.strftime('%Y-%m-%d'),
            'booking-checkout': self.tomorrow.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 200)
        form = response.context['booking_form']
        self.assertFalse(form.is_valid())
        self.assertIn('La fecha de salida debe ser posterior a la fecha de entrada', str(form.non_field_errors()))
    
    def test_post_with_same_checkin_checkout_shows_error(self):
        """Test that POST with checkin equal to checkout shows error"""
        post_data = {
            'booking-checkin': self.tomorrow.strftime('%Y-%m-%d'),
            'booking-checkout': self.tomorrow.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 200)
        form = response.context['booking_form']
        self.assertFalse(form.is_valid())
        self.assertIn('La fecha de salida debe ser posterior a la fecha de entrada', str(form.non_field_errors()))
    
    def test_post_with_missing_dates_shows_error(self):
        """Test that POST with missing dates shows error"""
        post_data = {
            'booking-checkin': '',
            'booking-checkout': ''
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 200)
        form = response.context['booking_form']
        self.assertFalse(form.is_valid())
        self.assertIn('checkin', form.errors)
        self.assertIn('checkout', form.errors)
    
    def test_post_updates_only_dates_not_other_fields(self):
        """Test that POST only updates dates, not other fields"""
        original_guests = self.booking.guests
        original_customer = self.booking.customer
        original_room = self.booking.room
        original_total = self.booking.total
        original_code = self.booking.code
        
        post_data = {
            'booking-checkin': self.day_after_tomorrow.strftime('%Y-%m-%d'),
            'booking-checkout': (self.day_after_tomorrow + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.guests, original_guests)
        self.assertEqual(self.booking.customer, original_customer)
        self.assertEqual(self.booking.room, original_room)
        self.assertEqual(self.booking.total, original_total)
        self.assertEqual(self.booking.code, original_code)
    
    def test_post_with_different_room_conflict(self):
        """Test conflicts with bookings in different rooms"""
    
        other_room = Room.objects.create(
            room_type=self.room_type,
            name="Test Room 102",
            description="Another test room"
        )
        
    
        conflicting_booking = Booking.objects.create(
            room=other_room,
            checkin=self.tomorrow + timedelta(days=2),
            checkout=self.tomorrow + timedelta(days=4),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=200.00,
            code="CONF002"
        )
        
    
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=1)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
    
        self.assertEqual(response.status_code, 302)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, self.tomorrow + timedelta(days=1))
    
    def test_post_with_conflicting_state_not_new(self):
        """Test that only bookings with state 'NEW' are considered conflicts"""
    
        non_conflicting_booking = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow + timedelta(days=2),
            checkout=self.tomorrow + timedelta(days=4),
            state=Booking.DELETED, 
            guests=2,
            customer=self.customer,
            total=200.00,
            code="CANCEL001"
        )
        
    
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=1)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
    
        self.assertEqual(response.status_code, 302)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, self.tomorrow + timedelta(days=1))


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UpdateBookingViewIntegrationTest(TestCase):
    """Integration tests for UpdateBookingView with multiple bookings"""
    
    def setUp(self):
        """Set up test data with multiple bookings"""
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        
    
        self.room_type = Room_type.objects.create(
            name="Suite",
            price=200.00,
            max_guests=4
        )
        
    
        self.room = Room.objects.create(
            room_type=self.room_type,
            name="Suite Test",
            description="Luxury suite"
        )
        
    
        self.customer = Customer.objects.create(
            name="Integration Test Customer",
            email="integration@example.com",
            phone="+9876543210"
        )
        
        self.booking1 = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow,
            checkout=self.tomorrow + timedelta(days=3),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=600.00,
            code="INT001"
        )
        
        self.booking2 = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow + timedelta(days=4),
            checkout=self.tomorrow + timedelta(days=6),
            state=Booking.NEW,
            guests=2,
            customer=self.customer,
            total=400.00,
            code="INT002"
        )
        
        self.url = reverse('update_booking', kwargs={'pk': self.booking1.id})
    
    def test_update_between_existing_bookings_success(self):
        """Test updating between two existing bookings succeeds"""
    
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=3)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=4)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 302)
        
        self.booking1.refresh_from_db()
        self.assertEqual(self.booking1.checkout, self.tomorrow + timedelta(days=4))
    
    def test_update_overlapping_existing_booking_fails(self):
        """Test that update overlapping with existing booking fails"""
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=2)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=5)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 200)
        form = response.context['booking_form']
        self.assertIn('No hay disponibilidad para las fechas seleccionadas', str(form.non_field_errors()))
    
    def test_update_exactly_adjacent_to_existing_booking_succeeds(self):
        """Test that update exactly adjacent to existing booking succeeds (no overlap)"""
        post_data = {
            'booking-checkin': (self.tomorrow + timedelta(days=3)).strftime('%Y-%m-%d'),
            'booking-checkout': (self.tomorrow + timedelta(days=4)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        
        self.assertEqual(response.status_code, 302)
        
    
        self.booking1.refresh_from_db()
        self.booking2.refresh_from_db()
        self.assertLessEqual(self.booking1.checkout, self.booking2.checkin)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UpdateBookingViewEdgeCasesTest(TestCase):
    """Edge cases tests for UpdateBookingView"""
    
    def setUp(self):
        """Set up test data for edge cases"""
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        
    
        self.room_type = Room_type.objects.create(
            name="Economy",
            price=50.00,
            max_guests=2
        )
        
    
        self.room = Room.objects.create(
            room_type=self.room_type,
            name="Economy Room",
            description="Budget room"
        )
        
    
        self.customer = Customer.objects.create(
            name="Edge Case Customer",
            email="edge@example.com",
            phone="+1111111111"
        )
        
        self.booking = Booking.objects.create(
            room=self.room,
            checkin=self.tomorrow,
            checkout=self.tomorrow + timedelta(days=3),
            state=Booking.NEW,
            guests=1,
            customer=self.customer,
            total=150.00,
            code="EDGE001"
        )
        
        self.url = reverse('update_booking', kwargs={'pk': self.booking.id})
    
    def test_update_with_boundary_dates(self):
        """Test updating with boundary dates (minimum and maximum allowed)"""
    
        min_checkin = self.tomorrow
        min_checkout = self.tomorrow + timedelta(days=1)
        
        post_data = {
            'booking-checkin': min_checkin.strftime('%Y-%m-%d'),
            'booking-checkout': min_checkout.strftime('%Y-%m-%d')
        }
        
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, min_checkin)
        self.assertEqual(self.booking.checkout, min_checkout)
    
    def test_update_with_maximum_range_in_same_year(self):
        """Test updating with maximum range within same year"""
    
        end_of_year = date(self.today.year, 12, 31)
        
        if end_of_year > self.tomorrow:
            post_data = {
                'booking-checkin': self.tomorrow.strftime('%Y-%m-%d'),
                'booking-checkout': end_of_year.strftime('%Y-%m-%d')
            }
            
            response = self.client.post(self.url, post_data)
            self.assertEqual(response.status_code, 302)
            
            self.booking.refresh_from_db()
            self.assertEqual(self.booking.checkout, end_of_year)
    
    def test_update_same_booking_multiple_times(self):
        """Test updating the same booking multiple times"""
    
        first_checkin = self.tomorrow + timedelta(days=1)
        first_checkout = self.tomorrow + timedelta(days=2)
        
        post_data1 = {
            'booking-checkin': first_checkin.strftime('%Y-%m-%d'),
            'booking-checkout': first_checkout.strftime('%Y-%m-%d')
        }
        
        response1 = self.client.post(self.url, post_data1)
        self.assertEqual(response1.status_code, 302)
        
    
        second_checkin = first_checkin + timedelta(days=1)
        second_checkout = first_checkout + timedelta(days=2)
        
        post_data2 = {
            'booking-checkin': second_checkin.strftime('%Y-%m-%d'),
            'booking-checkout': second_checkout.strftime('%Y-%m-%d')
        }
        
        response2 = self.client.post(self.url, post_data2)
        self.assertEqual(response2.status_code, 302)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.checkin, second_checkin)
        self.assertEqual(self.booking.checkout, second_checkout)
    
    