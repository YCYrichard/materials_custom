import frappe
from frappe import _
from frappe.model.document import Document


class DriverVehicleAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		driver: DF.Link
		driver_name: DF.Data | None
		naming_series: DF.Literal["MC-DVA-.YYYY.-"]
		remarks: DF.SmallText | None
		shift: DF.Literal["Morning", "Afternoon", "Full Day"]
		shift_date: DF.Date
		status: DF.Literal["Active", "Cancelled"]
		vehicle: DF.Link
	# end: auto-generated types

	def validate(self):
		if self.status != "Active":
			return

		self.check_conflict("driver", _("Driver"))
		self.check_conflict("vehicle", _("Vehicle"))

	def check_conflict(self, fieldname, label):
		conflict = frappe.db.exists(
			"Driver Vehicle Assignment",
			{
				fieldname: self.get(fieldname),
				"shift_date": self.shift_date,
				"shift": self.shift,
				"status": "Active",
				"name": ["!=", self.name],
			},
		)
		if conflict:
			frappe.throw(
				_("{0} {1} is already assigned for {2} shift on {3} ({4}).").format(
					label, self.get(fieldname), self.shift, self.shift_date, conflict
				)
			)
