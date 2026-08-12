import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate
from frappe.utils.user import get_users_with_role

WARNING_WINDOWS = [60, 30]


def check_expiring_credentials():
	"""Daily job: warn HR Manager about driver licenses and vehicle
	insurance/inspection expiring within 60 and 30 days."""
	users = get_users_with_role("HR Manager")
	if not users:
		return

	today = getdate(nowdate())

	for window in WARNING_WINDOWS:
		threshold = add_days(today, window)
		_notify_expiring_licenses(users, today, threshold, window)
		_notify_expiring_vehicle_dates(
			users, today, threshold, window, "end_date", _("insurance")
		)
		_notify_expiring_vehicle_dates(
			users, today, threshold, window, "custom_inspection_expiry", _("驗車 inspection")
		)


def _notify_expiring_licenses(users, today, threshold, window):
	rows = frappe.get_all(
		"Driving License Category",
		filters={
			"parenttype": "Driver",
			"expiry_date": ["between", [today, threshold]],
		},
		fields=["parent", "class", "expiry_date"],
	)
	for row in rows:
		driver_name = frappe.db.get_value("Driver", row.parent, "full_name") or row.parent
		_create_notification(
			users,
			document_type="Driver",
			document_name=row.parent,
			subject=_("Driver license expiring within {0} days").format(window),
			message=_("{0}'s {1} license category expires on {2}.").format(
				driver_name, row["class"] or "", row.expiry_date
			),
		)


def _notify_expiring_vehicle_dates(users, today, threshold, window, fieldname, label):
	vehicles = frappe.get_all(
		"Vehicle",
		filters={fieldname: ["between", [today, threshold]]},
		fields=["name", "license_plate", fieldname],
	)
	for vehicle in vehicles:
		_create_notification(
			users,
			document_type="Vehicle",
			document_name=vehicle.name,
			subject=_("Vehicle {0} expiring within {1} days").format(label, window),
			message=_("Vehicle {0}'s {1} expires on {2}.").format(
				vehicle.license_plate or vehicle.name, label, vehicle.get(fieldname)
			),
		)


def _create_notification(users, document_type, document_name, subject, message):
	for user in users:
		if frappe.db.exists(
			"Notification Log",
			{
				"for_user": user,
				"document_type": document_type,
				"document_name": document_name,
				"subject": subject,
			},
		):
			continue

		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"for_user": user,
				"document_type": document_type,
				"document_name": document_name,
				"subject": subject,
				"email_content": message,
			}
		).insert(ignore_permissions=True)
