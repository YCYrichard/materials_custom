import frappe
from frappe import _
from frappe.model.document import Document


class DriverIncidentLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Text
		driver: DF.Link
		driver_name: DF.Data | None
		incident_date: DF.Date
		incident_type: DF.Literal["Accident", "Violation", "Complaint", "Other"]
		naming_series: DF.Literal["MC-DIL-.YYYY.-"]
		related_delivery_trip: DF.Link | None
		reported_by: DF.Link | None
		resolution: DF.Text | None
		severity: DF.Literal["Minor", "Major", "Critical"]
		status: DF.Literal["Open", "Under Review", "Closed"]
		vehicle: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if self.status == "Closed" and not self.resolution:
			frappe.throw(_("Resolution is required before closing a Driver Incident Log."))
