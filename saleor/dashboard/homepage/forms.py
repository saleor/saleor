from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import pgettext_lazy
from mptt.fields import TreeNodeChoiceField

from ...product.models import Category
from ...homepage.models import HomePageItem


CATEGORY_LABEL = pgettext_lazy(
    'Homepage block linked category field label',
    'Category to link')


class BlockItemForm(forms.ModelForm):
    category = TreeNodeChoiceField(
        Category.objects.all(), required=False, label=CATEGORY_LABEL)

    class Meta:
        model = HomePageItem
        exclude = []
        labels = {
            'title': pgettext_lazy(
                'Homepage block title field label',
                'Title'),
            'subtitle': pgettext_lazy(
                'Homepage block subtitle field label',
                'Subtitle'),
            'primary_button_text': pgettext_lazy(
                'Homepage block primary button text field label',
                'Primary button text'),
            'html_classes': pgettext_lazy(
                'Homepage block html classes field label',
                'HTML classes'),
            'cover': pgettext_lazy(
                'Homepage block cover image field label',
                'Cover image'),
            'collection': pgettext_lazy(
                'Homepage block linked collection field label',
                'Collection to link'),
            'category': CATEGORY_LABEL,
            'page': pgettext_lazy(
                'Homepage block linked page field label',
                'Page to link')}

    def clean(self):
        cleaned_data = super().clean()

        required_fields = tuple(filter(None, (
            self.cleaned_data['page'],
            self.cleaned_data['category'],
            self.cleaned_data['collection']
        )))

        # if none of the required fields are filled
        if not required_fields:
            raise ValidationError(pgettext_lazy(
                'Home page block item creation/edit form error',
                'You must select <strong>an object</strong> to link to this '
                'block.'))

        # or if there was more than one filled
        if len(required_fields) > 1:
            raise ValidationError(pgettext_lazy(
                'Home page block item creation/edit form error',
                'You must select <strong>only one</strong> object to link to '
                'this block.'))

        return cleaned_data

    def save(self, commit=True):
        res = super(BlockItemForm, self).save(commit)
        if 'cover' in self.changed_data:
            res.create_thumbnails()
        return res
