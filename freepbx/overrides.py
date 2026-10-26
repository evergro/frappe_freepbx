import frappe


@frappe.whitelist()
def is_call_integration_enabled():
	"""CRM's own answer plus a `freepbx` flag read from FreePBX Settings."""
	from crm.integrations.api import is_call_integration_enabled as crm_default

	data = crm_default()
	data.setdefault("integrations", {})["freepbx"] = bool(
		frappe.db.get_single_value("FreePBX Settings", "enabled")
	)
	return data
