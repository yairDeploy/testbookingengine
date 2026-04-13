from django.test import TestCase
from django import forms
from datetime import date, datetime, timedelta
from unittest.mock import patch
from pms.forms import BookingFormDates
from pms.models import Booking


class BookingFormDatesTest(TestCase):
    """Unit tests BookingFormDates"""
    
    def setUp(self):
        """Initial setup for tests"""
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)
    
    def test_form_is_valid_with_valid_dates(self):
        """Test that the form is valid with correct dates"""
        form_data = {
            'checkin': self.tomorrow.strftime('%Y-%m-%d'),
            'checkout': self.next_week.strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_when_checkout_equals_checkin(self):
        """Test that the form is invalid when checkout equals checkin"""
        form_data = {
            'checkin': self.tomorrow.strftime('%Y-%m-%d'),
            'checkout': self.tomorrow.strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(
            form.non_field_errors()[0],
            'La fecha de salida debe ser posterior a la fecha de entrada'
        )
    
    def test_form_invalid_when_checkout_earlier_than_checkin(self):
        """Test that the form is invalid when checkout is earlier than checkin"""
        form_data = {
            'checkin': self.tomorrow.strftime('%Y-%m-%d'),
            'checkout': self.today.strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(
            form.non_field_errors()[0],
            'La fecha de salida debe ser posterior a la fecha de entrada'
        )
    
    def test_form_clean_method_handles_missing_checkin(self):
        """Test that clean() handles missing checkin correctly"""
        form_data = {
            'checkout': self.tomorrow.strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        # The form will be invalid due to missing fields, but it should not raise an exception
        self.assertFalse(form.is_valid())
        self.assertIn('checkin', form.errors)
    
    def test_form_clean_method_handles_missing_checkout(self):
        """Test that clean() handles missing checkout correctly"""
        form_data = {
            'checkin': self.tomorrow.strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('checkout', form.errors)
    
    def test_form_clean_method_handles_none_dates(self):
        """Test that clean() handles None dates correctly"""
        form_data = {
            'checkin': None,
            'checkout': None
        }
        form = BookingFormDates(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_form_widget_attributes(self):
        """Test that the widgets have the correct attributes"""
        form = BookingFormDates()
        
        # Verify checkin widget
        checkin_widget = form.fields['checkin'].widget
        # The 'type' attribute may not exist, we check for 'min' and 'id'
        self.assertEqual(checkin_widget.attrs.get('id'), 'id_checkin')
        self.assertIn('min', checkin_widget.attrs)
        
        # Verify checkout widget
        checkout_widget = form.fields['checkout'].widget
        self.assertEqual(checkout_widget.attrs.get('id'), 'id_checkout')
        self.assertIn('max', checkout_widget.attrs)
    
    def test_form_widget_has_correct_attrs(self):
        """Test that the widgets have the correct attribute configuration"""
        form = BookingFormDates()
        
        # Verify that the widgets are of the correct type
        self.assertIsInstance(form.fields['checkin'].widget, forms.DateInput)
        self.assertIsInstance(form.fields['checkout'].widget, forms.DateInput)
        
        # Verify specific attributes
        self.assertEqual(form.fields['checkin'].widget.attrs.get('id'), 'id_checkin')
        self.assertEqual(form.fields['checkout'].widget.attrs.get('id'), 'id_checkout')
    
    def test_checkin_min_date_is_today(self):
        """Test that the min attribute of checkin is today's date"""
        # No need to mock, we use the real date
        form = BookingFormDates()
        today_str = date.today().strftime('%Y-%m-%d')
        self.assertEqual(form.fields['checkin'].widget.attrs.get('min'), today_str)
    
    def test_checkout_max_date_is_dec_31_current_year(self):
        """Test that the max attribute of checkout is December 31 of the current year"""
        form = BookingFormDates()
        current_year = date.today().year
        expected_max = date(current_year, 12, 31).strftime('%Y-%m-%d')
        self.assertEqual(form.fields['checkout'].widget.attrs.get('max'), expected_max)
    
    def test_form_accepts_valid_date_range(self):
        """Test that the form accepts a valid date range"""
        valid_ranges = [
            (self.today + timedelta(days=1), self.today + timedelta(days=2)),
            (self.today + timedelta(days=1), self.today + timedelta(days=30)),
            (self.today + timedelta(days=5), self.today + timedelta(days=10)),
        ]
        
        for checkin, checkout in valid_ranges:
            form_data = {
                'checkin': checkin.strftime('%Y-%m-%d'),
                'checkout': checkout.strftime('%Y-%m-%d')
            }
            form = BookingFormDates(data=form_data)
            self.assertTrue(form.is_valid(), f"Failed for range {checkin} to {checkout}")
    
    def test_form_rejects_invalid_date_range(self):
        """Test that the form rejects invalid date ranges"""
        invalid_ranges = [
            (self.today + timedelta(days=1), self.today + timedelta(days=1)),  # iguales
            (self.today + timedelta(days=2), self.today + timedelta(days=1)),  # checkout menor
            (self.today, self.today),  # iguales incluyendo hoy
            (self.today + timedelta(days=5), self.today + timedelta(days=3)),  # checkout menor
        ]
        
        for checkin, checkout in invalid_ranges:
            form_data = {
                'checkin': checkin.strftime('%Y-%m-%d'),
                'checkout': checkout.strftime('%Y-%m-%d')
            }
            form = BookingFormDates(data=form_data)
            self.assertFalse(form.is_valid(), f"Should be invalid for range {checkin} to {checkout}")
            self.assertIn('__all__', form.errors)
    
    def test_form_meta_fields(self):
        """Test that the Meta has the correct fields"""
        form = BookingFormDates()
        self.assertEqual(list(form.Meta.fields), ['checkin', 'checkout'])
        self.assertEqual(form.Meta.model, Booking)


class BookingFormDatesEdgeCasesTest(TestCase):
    """Tests for edge cases of the BookingFormDates form"""
    
    def test_form_with_dates_in_same_year(self):
        """Test with dates within the same year"""
        today = date.today()
        form_data = {
            'checkin': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            'checkout': (today + timedelta(days=10)).strftime('%Y-%m-%d')
        }
        form = BookingFormDates(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_requires_future_checkin(self):
        """Test that the checkin must be in the future (due to the min attribute of the widget)"""
        form = BookingFormDates()
        min_date = form.fields['checkin'].widget.attrs.get('min')
        self.assertIsNotNone(min_date)
        
        # Verify that min_date is equal to or after today
        min_date_obj = datetime.strptime(min_date, '%Y-%m-%d').date()
        self.assertGreaterEqual(min_date_obj, date.today())
    
    def test_form_limits_checkout_to_current_year(self):
        """Test that the checkout is limited to the current year"""
        form = BookingFormDates()
        max_date = form.fields['checkout'].widget.attrs.get('max')
        self.assertIsNotNone(max_date)
        
        # Verify that max_date is December 31 of the current year
        max_date_obj = datetime.strptime(max_date, '%Y-%m-%d').date()
        current_year = date.today().year
        self.assertEqual(max_date_obj.year, current_year)
        self.assertEqual(max_date_obj.month, 12)
        self.assertEqual(max_date_obj.day, 31)