from django.forms import widgets
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt


class StringInput( widgets.TextInput ):
    input_type = 'text'


class Textarea( widgets.Textarea ):
    pass


class TwoItemFloatWidget( widgets.MultiWidget ):
    def __init__(self, attrs=None):
        multi_widget = (
            widgets.TextInput(attrs=attrs),
            widgets.TextInput(attrs=attrs)
        )
        super(TwoItemFloatWidget, self).__init__(multi_widget, attrs)

    def decompress(self, value):
        if value:
            return value.split(';')
        return [None, None]


class FourItemFloatWidget( widgets.MultiWidget ):
    def __init__(self, attrs=None):
        multi_widget = (
            widgets.TextInput(attrs=attrs),
            widgets.TextInput(attrs=attrs),
            widgets.TextInput(attrs=attrs),
            widgets.TextInput(attrs=attrs)
        )
        super(FourItemFloatWidget, self).__init__(multi_widget, attrs)

    def decompress(self, value):
        if value:
            return value.split(';')
        return [None, None]


class DistanceWidget( TwoItemFloatWidget ):
    def decompress(self, value):
        if value:
            return [None if x == '-' else x for x in value.split(';')]

        return [None, None]


class SubjectCategoryWidget( widgets.TextInput ):
    input_type = 'hidden'

    def generateFlex(self):
        flex_code = u"""
            <link rel="stylesheet" type="text/css" href="/static/media/flex/history/history.css" />
            <script src="/static/media/flex/AC_OETags.js" language="javascript"></script>
            <script src="/static/media/flex/history/history.js" language="javascript"></script>
            <script src="/static/media/flex/jquery-1.3.2.min.js" language="javascript"></script>

            <script language="JavaScript" type="text/javascript">
            // -----------------------------------------------------------------------------
            // Globals
            // Major version of Flash required
            var requiredMajorVersion = 9;
            // Minor version of Flash required
            var requiredMinorVersion = 0;
            // Minor version of Flash required
            var requiredRevision = 124;
            // -----------------------------------------------------------------------------
            //
            </script>
            <script language="JavaScript" type="text/javascript">
            // Version check for the Flash Player that has the ability to start Player Product Install (6.0r65)
            var hasProductInstall = DetectFlashVer(6, 0, 65);

            // Version check based upon the values defined in globals
            var hasRequestedVersion = DetectFlashVer(requiredMajorVersion, requiredMinorVersion, requiredRevision);

            if ( hasProductInstall && !hasRequestedVersion ) {
                // DO NOT MODIFY THE FOLLOWING FOUR LINES
                // Location visited after installation is complete if installation is required
                var MMPlayerType = (isIE == true) ? "ActiveX" : "PlugIn";
                var MMredirectURL = window.location;
                document.title = document.title.slice(0, 47) + " - Flash Player Installation";
                var MMdoctitle = document.title;

                AC_FL_RunContent(
                    "src", "playerProductInstall",
                    "FlashVars", "MMredirectURL="+MMredirectURL+'&MMplayerType='+MMPlayerType+'&MMdoctitle='+MMdoctitle+"",
                    "width", "100%",
                    "height", "100%",
                    "align", "middle",
                    "id", "DjangoSubjectCategory",
                    "quality", "high",
                    "bgcolor", "#869ca7",
                    "name", "DjangoSubjectCategory",
                    "allowScriptAccess","sameDomain",
                    "type", "application/x-shockwave-flash",
                    "pluginspage", "http://www.adobe.com/go/getflashplayer"
                );
            } else if (hasRequestedVersion) {
                // if we've detected an acceptable version
                // embed the Flash Content SWF when all tests are passed
                AC_FL_RunContent(
                        "src", "/static/media/flex/DjangoSubjectCategory",
                        "width", "700",
                        "height", "245",
                        "align", "middle",
                        "id", "DjangoSubjectCategory",
                        "quality", "high",
                        "bgcolor", "#869ca7",
                        "name", "DjangoSubjectCategory",
                        "allowScriptAccess","sameDomain",
                        "type", "application/x-shockwave-flash",
                        "pluginspage", "http://www.adobe.com/go/getflashplayer"
                );
              } else {  // flash is too old or we can't detect the plugin
                var alternateContent = 'Alternate HTML content should be placed here. '
                  + 'This content requires the Adobe Flash Player. '
                   + '<a href=http://www.adobe.com/go/getflash/>Get Flash</a>';
                document.write(alternateContent);  // insert non-flash content
              }
            </script>
            <div>
            <noscript>
                  <object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"
                        id="DjangoSubjectCategory" width="700" height="245"
                        codebase="http://fpdownload.macromedia.com/get/flashplayer/current/swflash.cab">
                        <param name="movie" value="/static/media/flex/DjangoSubjectCategory.swf" />
                        <param name="quality" value="high" />
                        <param name="bgcolor" value="#869ca7" />
                        <param name="allowScriptAccess" value="sameDomain" />
                        <embed src="/static/media/flex/DjangoSubjectCategory.swf" quality="high" bgcolor="#869ca7"
                            width="700" height="245" name="DjangoSubjectCategory" align="middle"
                            play="true"
                            loop="false"
                            quality="high"
                            allowScriptAccess="sameDomain"
                            type="application/x-shockwave-flash"
                            pluginspage="http://www.adobe.com/go/getflashplayer">
                        </embed>
                </object>
            </noscript>
            </div>
            """
        return flex_code

    def generateJS(self):
        js = """
            <script language="JavaScript" type="text/javascript">

            function flexToJS(data) {
                $(document).ready(function() {
                    $("#id_subject_category").attr("value", data);
                });
            }

            function JSToFlex() {
                $(document).ready(function() {
                    data = $("#id_subject_category").attr("value");
                    return data;
                });
            }

            </script>
        """
        return js

    def render(self, name, value, attrs=None):
        flex = self.generateFlex()
        js = self.generateJS()
        if value is None:
            value = ''
        if attrs is None:
            attrs = {}
        final_attrs = self.build_attrs(attrs,
            {'type': self.input_type, 'name': name})
        if value != '':
            final_attrs['value'] = force_text(value)

        default_html = u'<input%s />' % flatatt(final_attrs)
        return mark_safe(flex + js + default_html)
