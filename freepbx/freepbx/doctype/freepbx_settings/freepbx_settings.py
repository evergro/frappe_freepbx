import frappe
from frappe import _
from frappe.model.document import Document


class FreePBXSettings(Document):
	def validate(self):
		self.pbx_domain = (self.pbx_domain or "").strip().lower()
		self.wss_url = (self.wss_url or "").strip()

		if not self.enabled:
			return

		if not self.pbx_domain:
			frappe.throw(_("PBX Domain is required when FreePBX is enabled."))

		if not self.wss_url:
			self.wss_url = f"wss://{self.pbx_domain}:8089/ws"

		if not self.wss_url.startswith("wss://"):
			frappe.throw(_("The WebSocket URL must start with wss:// (browsers block plain ws:// on HTTPS sites)."))

		for field in ("country_code", "national_prefix", "international_prefix"):
			value = (self.get(field) or "").strip()
			if value and not value.isdigit():
				frappe.throw(_("{0} must contain digits only.").format(self.meta.get_label(field)))
			self.set(field, value)
