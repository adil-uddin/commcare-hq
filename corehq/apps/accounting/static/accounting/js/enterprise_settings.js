hqDefine("accounting/js/enterprise_settings", [
    'jquery',
    'knockout',
    'underscore',
    'hqwebapp/js/assert_properties',
    'hqwebapp/js/initial_page_data',
], function(
    $,
    ko,
    _,
    assertProperties,
    initialPageData
) {
    var settingsFormModel = function(options) {
        assertProperties.assert(options, ['accounts_email'], ['restrict_signup', 'restricted_domains']);

        var self = {};

        self.restrictSignup = ko.observable(options.restrict_signup);
        self.restrictSignupHelp = _.template(gettext("Do not allow new users to sign up on commcarehq.org." +
            "<br>This will affect users with email addresses from the following domains: " +
            "<strong><%= domains %></strong>" +
            "<br>Contact <a href='mailto:<%= email %>'><%= email %></a> to change the list of domains."))({
                domains: options.restricted_domains.join(", "),
                email: options.accounts_email,
        });

        return self;
    };

    $(function() {
        var form = settingsFormModel({
            accounts_email: initialPageData.get('accounts_email'),
            restricted_domains: initialPageData.get('restricted_domains'),
            restrict_signup: initialPageData.get('restrict_signup'),
        });
        $('#enterprise-settings-form').koApplyBindings(form);
    });
});
