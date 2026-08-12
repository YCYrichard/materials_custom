import frappe
from frappe import _
from frappe.utils import getdate

# custom_dispatch_status values that represent an active dispatch — the trip
# has (or had) a driver and vehicle actually on the road, as opposed to
# "Pending" (not yet assigned) or "Failed" (a recorded outcome that must
# always be writable regardless of credential status).
GATED_STATUSES = {"Assigned", "In Transit", "Delivered"}


def validate_dispatch_eligibility(doc, method=None):
	dispatch_status = doc.get("custom_dispatch_status")
	if dispatch_status not in GATED_STATUSES:
		return

	trip_date = getdate(doc.departure_time) if doc.departure_time else getdate()

	if not doc.driver:
		frappe.throw(_("A Driver must be assigned before this trip can move to {0}.").format(dispatch_status))

	_check_driver_license(doc.driver, trip_date)
	_check_vehicle_credentials(doc.vehicle, trip_date)


def _check_driver_license(driver, trip_date):
	license_rows = frappe.get_all(
		"Driving License Category",
		filters={"parenttype": "Driver", "parent": driver},
		fields=["expiry_date"],
	)

	valid = any(row.expiry_date and getdate(row.expiry_date) >= trip_date for row in license_rows)

	if not valid:
		frappe.throw(
			_(
				"Driver {0} has no driving license category valid on {1}. "
				"A Delivery Trip cannot be assigned to a driver with an expired or missing license."
			).format(frappe.bold(driver), trip_date)
		)


def _check_vehicle_credentials(vehicle, trip_date):
	vehicle_doc = frappe.db.get_value(
		"Vehicle", vehicle, ["end_date", "custom_inspection_expiry"], as_dict=True
	)

	if not vehicle_doc or not vehicle_doc.end_date or getdate(vehicle_doc.end_date) < trip_date:
		frappe.throw(
			_(
				"Vehicle {0} does not have valid insurance on {1}. "
				"A Delivery Trip cannot use a vehicle with expired or missing insurance."
			).format(frappe.bold(vehicle), trip_date)
		)

	if not vehicle_doc.custom_inspection_expiry or getdate(vehicle_doc.custom_inspection_expiry) < trip_date:
		frappe.throw(
			_(
				"Vehicle {0} does not have a valid 驗車 (inspection) on {1}. "
				"A Delivery Trip cannot use a vehicle with an expired or missing inspection."
			).format(frappe.bold(vehicle), trip_date)
		)
