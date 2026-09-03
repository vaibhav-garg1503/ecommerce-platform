from django import forms

class BulkImportForm(forms.Form):
    """Form for uploading a CSV file to bulk import products."""
    csv_file = forms.FileField(
        label="Select CSV File",
        help_text="Upload a .csv file formatted according to the catalog template."
    )


class RestockForm(forms.Form):
    """Form for quickly restocking a product variant."""
    variant_id = forms.IntegerField(widget=forms.HiddenInput)
    add_qty = forms.IntegerField(min_value=1, label="Quantity to Add")
