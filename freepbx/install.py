import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

MEDIUM = "FreePBX"

AGENT_FIELDS = {
	"CRM Telephony Agent": [
		{
			"fieldname": "freepbx_section",
			"label": "FreePBX",
			"fieldtype": "Section Break",
			"insert_after": "call_receiving_device",
		},
		{
			"fieldname": "freepbx_extension",
			"label": "FreePBX Extension",
			"fieldtype": "Data",
			"insert_after": "freepbx_section",
			"description": "WebRTC extension this agent's browser registers as (digits only).",
		},
		{
			"fieldname": "freepbx_password",
			"label": "FreePBX Extension Password",
			"fieldtype": "Password",
			"insert_after": "freepbx_extension",
			"description": "The extension's SIP secret from FreePBX. Stored encrypted.",
		},
	]
}


def after_install():
	setup_crm()


def after_migrate():
	setup_crm()


def setup_crm():
	"""Idempotent: safe to run on every migrate."""
	if not frappe.db.exists("DocType", "CRM Telephony Agent"):
		return

	create_custom_fields(AGENT_FIELDS, ignore_validate=True)
	add_select_option("CRM Telephony Agent", "default_medium", MEDIUM)
	add_select_option("CRM Call Log", "telephony_medium", MEDIUM)


def add_select_option(doctype: str, fieldname: str, option: str):
	field = frappe.get_meta(doctype).get_field(fieldname)
	if not field:
		return

	options = (field.options or "").split("\n")
	if option in options:
		return

	options.append(option)
	make_property_setter(doctype, fieldname, "options", "\n".join(options), "Text")
