app_name = "freepbx"
app_title = "Freepbx"
app_publisher = "Evergro Digital"
app_description = "Freepbx Sip intergration to Frappe"
app_email = "hello@digital.evergro.co.za"
app_license = "agpl-3.0"

# The CRM app provides the call popup, call logs and telephony agents we extend.
required_apps = ["crm"]

# Adds the "FreePBX" calling medium to CRM and the agent fields it needs.
# Both run again on every `bench migrate`, so a CRM upgrade cannot undo them.
after_install = "freepbx.install.after_install"
after_migrate = "freepbx.install.after_migrate"

# Tell the CRM frontend that FreePBX is an enabled call integration, without
# editing crm.integrations.api in the CRM fork.
override_whitelisted_methods = {
	"crm.integrations.api.is_call_integration_enabled": "freepbx.overrides.is_call_integration_enabled",
}

doc_events = {
	"CRM Telephony Agent": {
		"validate": "freepbx.events.validate_agent",
	},
}
