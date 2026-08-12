import frappe
from frappe import _
from frappe.utils import flt

DISTANCE_BONUS_COMPONENT = "Delivery Distance Bonus"


@frappe.whitelist()
def create_distance_bonus_additional_salary(employee: str, from_date: str, to_date: str):
	"""Sum the distance of Delivered trips for `employee` between from_date and
	to_date, and create (or update) an Additional Salary record for the
	Delivery Distance Bonus component covering that period. Rate is read
	from Materials Custom Settings — the bonus is skipped entirely if the
	rate is unconfigured, rather than silently paying 0."""

	rate = flt(frappe.db.get_single_value("Materials Custom Settings", "distance_bonus_rate"))
	if not rate:
		frappe.throw(
			_(
				"Distance Bonus Rate (per km) is not configured in Materials Custom Settings. "
				"Set it before generating delivery distance bonuses."
			)
		)

	total_distance = frappe.db.sql(
		"""
		select sum(total_distance)
		from `tabDelivery Trip`
		where employee = %(employee)s
			and custom_dispatch_status = 'Delivered'
			and departure_time between %(from_date)s and %(to_date)s
		""",
		{"employee": employee, "from_date": from_date, "to_date": to_date},
	)[0][0] or 0

	if not total_distance:
		return None

	amount = flt(total_distance) * rate
	company = frappe.db.get_value("Employee", employee, "company")

	existing = frappe.db.exists(
		"Additional Salary",
		{
			"employee": employee,
			"salary_component": DISTANCE_BONUS_COMPONENT,
			"payroll_date": to_date,
			"docstatus": ["!=", 2],
		},
	)
	if existing:
		# Never silently mutate a payroll record that already exists (draft or
		# submitted) — surface it so a human decides whether to amend it.
		return frappe.get_doc("Additional Salary", existing)

	additional_salary = frappe.get_doc(
		{
			"doctype": "Additional Salary",
			"employee": employee,
			"company": company,
			"salary_component": DISTANCE_BONUS_COMPONENT,
			"type": "Earning",
			"amount": amount,
			"is_recurring": 0,
			"payroll_date": to_date,
			"overwrite_salary_structure_amount": 1,
		}
	)
	additional_salary.insert(ignore_permissions=True)
	return additional_salary
