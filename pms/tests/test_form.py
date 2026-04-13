rom django.test import TestCase
from pms.form_filters.name_form import NameForm
class NameFormTest(TestCase):
	def test_valid_name(self):
		form = NameForm(data={'name': 'Juan Perez'})
		self.assertTrue(form.is_valid())
	def test_empty_name(self):
		form = NameForm(data={'name': ''})
		self.assertFalse(form.is_valid())
		self.assertIn('name', form.errors)
	def test_name_too_long(self):
		long_name = 'a' * 101
		form = NameForm(data={'name': long_name})
		self.assertFalse(form.is_valid())
		self.assertIn('name', form.errors)
	def test_widget_attrs(self):
		form = NameForm()
		self.assertIn('class', form.fields['name'].widget.attrs)
		self.assertEqual(form.fields['name'].widget.attrs['class'], 'form-control')
