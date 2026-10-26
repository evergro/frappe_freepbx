import frappe
from frappe import _


def validate_agent(doc, method=None):
	"""Keep FreePBX extensions clean and unique per CRM Telephony Agent."""
	extension = (doc.get("freepbx_extension") or "").strip()
	doc.freepbx_extension = extension

	if doc.get("default_medium") == "FreePBX" and not extension:
		frappe.throw(_("Set a FreePBX extension before choosing FreePBX as the default medium."))

	if not extension:
		return

	if not extension.isdigit() or len(extension) > 8:
		frappe.throw(_("The FreePBX extension must be 2-8 digits, for example 305."))

	taken = frappe.db.get_value(
		"CRM Telephony Agent",
		{"freepbx_extension": extension, "name": ("!=", doc.name)},
		"name",
	)
	if taken:
		frappe.throw(_("Extension {0} is already assigned to {1}.").format(extension, taken))
