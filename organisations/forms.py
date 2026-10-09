from django import forms

from organisations.models import Group


class NewGroupForm(forms.ModelForm):
    """✨ The "New group" form on "Your organisations": a name and a type. The organisation comes from the address."""

    # ✨ Declared so the choice is two radio buttons with Cohort already chosen, rather than a list with a blank row.
    type = forms.ChoiceField(choices=Group.Type.choices, initial=Group.Type.COHORT, widget=forms.RadioSelect)

    class Meta:
        model = Group
        fields = ["name", "type"]
