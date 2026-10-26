import re

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_seconds

STATUS_RANK = {
	"Initiated": 0,
	"Queued": 0,
	"Ringing": 1,
	"In Progress": 2,
	"Completed": 3,
	"Failed": 3,
	"Busy": 3,
	"No Answer": 3,
	"Canceled": 3,
}
TERMINAL = {"Completed", "Failed", "Busy", "No Answer", "Canceled"}


def _get_agent():
	"""The logged-in user's own CRM Telephony Agent, or None."""
	user = frappe.session.user
	if not frappe.db.exists("CRM Telephony Agent", user):
		return None
	return frappe.get_doc("CRM Telephony Agent", user)


def _require_agent():
	agent = _get_agent()
	if not agent or not agent.get("freepbx_extension"):
		frappe.throw(_("No FreePBX extension is set for your user."), frappe.PermissionError)
	return agent


def _clean_number(number: str) -> str:
	"""CRM Call Log validates from/to as phone numbers, so keep only valid characters."""
	cleaned = re.sub(r"[^0-9+*#()\-. ]", "", str(number or ""))[:20].strip()
	return cleaned or "0"


@frappe.whitelist(methods=["POST"])
def get_sip_config():
	"""Connection details for the *calling user's own* extension only."""
	settings = frappe.get_single("FreePBX Settings")
	if not settings.enabled:
		return {"configured": False}

	agent = _get_agent()
	if not agent:
		return {"configured": False}

	extension = (agent.get("freepbx_extension") or "").strip()
	password = agent.get_password("freepbx_password", raise_exception=False)
	if not (extension and password):
		return {"configured": False}

	return {
		"configured": True,
		"domain": settings.pbx_domain,
		"wss_url": settings.wss_url or f"wss://{settings.pbx_domain}:8089/ws",
		"stun": (settings.stun_server or "").strip(),
		"extension": extension,
		"password": password,
		"display_name": frappe.db.get_value("User", frappe.session.user, "full_name") or extension,
		"country_code": settings.country_code or "",
		"national_prefix": settings.national_prefix or "",
		"international_prefix": settings.international_prefix or "",
	}


@frappe.whitelist(methods=["POST"])
def create_call_log(number: str, direction: str):
	"""Create the CRM Call Log for a call that is starting. Returns its name."""
	agent = _require_agent()
	if direction not in ("Incoming", "Outgoing"):
		frappe.throw(_("Invalid call direction"))

	remote = _clean_number(number)
	extension = agent.freepbx_extension
	outgoing = direction == "Outgoing"
	user = frappe.session.user

	call_log = frappe.get_doc(
		{
			"doctype": "CRM Call Log",
			"id": frappe.generate_hash(length=12),
			"type": direction,
			"status": "Initiated" if outgoing else "Ringing",
			"telephony_medium": "FreePBX",
			"medium": extension,
			"from": extension if outgoing else remote,
			"to": remote if outgoing else extension,
			"caller": user if outgoing else None,
			"receiver": None if outgoing else user,
			"start_time": now_datetime(),
		}
	)
	_link_reference(call_log, remote)
	call_log.insert(ignore_permissions=True)
	return call_log.name


@frappe.whitelist(methods=["POST"])
def update_call_log(call_id: str, status: str):
	"""Move a call log forward (Ringing -> In Progress -> final status).

	Times and duration are taken from the server clock, not the browser's.
	"""
	if status not in STATUS_RANK:
		frappe.throw(_("Invalid call status"))

	call_log = frappe.get_doc("CRM Call Log", call_id)
	user = frappe.session.user
	if call_log.telephony_medium != "FreePBX" or user not in (call_log.caller, call_log.receiver):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# Never move a call backwards (a late "Ringing" must not undo "In Progress").
	if STATUS_RANK[status] <= STATUS_RANK.get(call_log.status, 0) and status != call_log.status:
		return {"name": call_log.name, "status": call_log.status}
	if call_log.status in TERMINAL:
		return {"name": call_log.name, "status": call_log.status}

	now = now_datetime()
	call_log.status = status

	if status == "In Progress":
		call_log.start_time = now  # answer time
	elif status in TERMINAL:
		call_log.end_time = now
		if status == "Completed" and call_log.start_time:
			call_log.duration = max(0, int(time_diff_in_seconds(now, call_log.start_time)))

	call_log.save(ignore_permissions=True)
	return {"name": call_log.name, "status": call_log.status}


def _link_reference(call_log, number: str):
	"""Link the call to the matching Contact, Lead or Deal, like the Twilio integration does."""
	from crm.integrations.api import get_contact_by_phone_number

	try:
		contact = get_contact_by_phone_number(number)
	except Exception:
		frappe.log_error(title="FreePBX: contact lookup failed")
		return

	if not contact.get("name"):
		return

	doctype, docname = "Contact", contact.get("name")
	if contact.get("lead"):
		doctype, docname = "CRM Lead", contact.get("lead")
	elif contact.get("deal"):
		doctype, docname = "CRM Deal", contact.get("deal")
	call_log.link_with_reference_doc(doctype, docname)
