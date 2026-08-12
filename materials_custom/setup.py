import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_migrate():
	create_custom_fields(get_custom_fields(), update=True)
	setup_delivery_trip_workflow()
	setup_dispatch_kanban()
	setup_salary_components()


DELIVERY_TRIP_WORKFLOW = "Delivery Trip Dispatch"

DISPATCH_STATES = ["Pending", "Assigned", "In Transit", "Delivered", "Failed"]

DISPATCH_TRANSITIONS = [
	# state, action, next_state
	("Pending", "Assign", "Assigned"),
	("Assigned", "Start Transit", "In Transit"),
	("In Transit", "Mark Delivered", "Delivered"),
	("Pending", "Mark Failed", "Failed"),
	("Assigned", "Mark Failed", "Failed"),
	("In Transit", "Mark Failed", "Failed"),
]

DISPATCH_ROLE = "Delivery Manager"


def setup_delivery_trip_workflow():
	if frappe.db.exists("Workflow", DELIVERY_TRIP_WORKFLOW):
		return

	for state in DISPATCH_STATES:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(
				ignore_permissions=True
			)

	for _state, action, _next_state in DISPATCH_TRANSITIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)

	workflow = frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": DELIVERY_TRIP_WORKFLOW,
			"document_type": "Delivery Trip",
			"is_active": 1,
			"workflow_state_field": "custom_dispatch_status",
			"states": [
				{"state": state, "doc_status": "0", "allow_edit": DISPATCH_ROLE} for state in DISPATCH_STATES
			],
			"transitions": [
				{
					"state": state,
					"action": action,
					"next_state": next_state,
					"allowed": DISPATCH_ROLE,
				}
				for state, action, next_state in DISPATCH_TRANSITIONS
			],
		}
	)
	workflow.insert(ignore_permissions=True)


DISPATCH_KANBAN = "Delivery Dispatch Board"

DISPATCH_KANBAN_COLUMNS = [
	("Pending", "Gray"),
	("Assigned", "Blue"),
	("In Transit", "Orange"),
	("Delivered", "Green"),
	("Failed", "Red"),
]


def setup_dispatch_kanban():
	if frappe.db.exists("Kanban Board", DISPATCH_KANBAN):
		return

	frappe.get_doc(
		{
			"doctype": "Kanban Board",
			"kanban_board_name": DISPATCH_KANBAN,
			"reference_doctype": "Delivery Trip",
			"field_name": "custom_dispatch_status",
			"private": 0,
			"columns": [
				{"column_name": name, "status": "Active", "indicator": color}
				for name, color in DISPATCH_KANBAN_COLUMNS
			],
		}
	).insert(ignore_permissions=True)


def setup_salary_components():
	if frappe.db.exists("Salary Component", "Delivery Distance Bonus"):
		return

	frappe.get_doc(
		{
			"doctype": "Salary Component",
			"salary_component": "Delivery Distance Bonus",
			"type": "Earning",
			"description": "Performance bonus based on distance driven on Delivered trips. "
			"Amount is injected per payroll period via Additional Salary by "
			"materials_custom.payroll.create_distance_bonus_additional_salary, "
			"using the rate configured in Materials Custom Settings.",
			"depends_on_payment_days": 0,
			"amount_based_on_formula": 0,
			"do_not_include_in_total": 0,
			"statistical_component": 0,
		}
	).insert(ignore_permissions=True)


def get_custom_fields():
	return {
		"Driver": [
			{
				"fieldname": "custom_years_of_experience",
				"fieldtype": "Int",
				"label": "Years of Experience",
				"insert_after": "status",
				"non_negative": 1,
			},
		],
		"Vehicle": [
			{
				"fieldname": "custom_inspection_expiry",
				"fieldtype": "Date",
				"label": "驗車到期日 (Inspection Expiry)",
				"insert_after": "end_date",
			},
		],
		"Delivery Trip": [
			{
				"fieldname": "custom_dispatch_status",
				"fieldtype": "Select",
				"label": "Dispatch Status",
				"options": "Pending\nAssigned\nIn Transit\nDelivered\nFailed",
				"default": "Pending",
				"insert_after": "status",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
			},
		],
	}
