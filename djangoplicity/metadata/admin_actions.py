from django.utils.html import format_html_join
from django.utils.translation import ugettext_lazy as _

# ============================================
# Mixin
# ============================================
class SetProgramMixin(object): # noqa
    def action_set_program(self, request, queryset, program=None):
        """
        Action method for set programs to Content
        """
        if program:
            for obj in queryset:
                obj.programs.add(program)

    def _make_program_action(self, program): # noqa
        """
        Helper method to define an admin action for a specific program
        """
        name = 'set_program_%s' % program.url

        def action(modeladmin, request, queryset):
            return modeladmin.action_set_program(request, queryset, program=program)

        return name, (action, name, "Set program %s" % str(program))

    def get_programs(self, obj):
        return "<br>".join([program.name for program in obj.programs.all()])

    get_programs.short_description = _("Programs")
    get_programs.allow_tags = True
