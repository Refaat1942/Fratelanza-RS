-- Table: attendance

CREATE TABLE attendance (
	id SERIAL NOT NULL, 
	employee_id INTEGER NOT NULL, 
	date VARCHAR(20) NOT NULL, 
	check_in VARCHAR(20), 
	check_out VARCHAR(20), 
	status VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
)

;

-- Table: audit_logs

CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	company_id INTEGER, 
	user_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	module VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100), 
	entity_id INTEGER, 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(500), 
	details TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

-- Table: bank_accounts

CREATE TABLE bank_accounts (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	bank_name VARCHAR(255) NOT NULL, 
	account_number VARCHAR(100) NOT NULL, 
	iban VARCHAR(50), 
	currency VARCHAR(10) NOT NULL, 
	balance NUMERIC(14, 2) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
)

;

-- Table: branches

CREATE TABLE branches (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	address TEXT, 
	city VARCHAR(100), 
	phone VARCHAR(50), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
)

;

-- Table: broker_commissions

CREATE TABLE broker_commissions (
	id SERIAL NOT NULL, 
	broker_id INTEGER NOT NULL, 
	contract_id INTEGER NOT NULL, 
	amount NUMERIC(14, 2) NOT NULL, 
	status commissionstatus NOT NULL, 
	approved_by_id INTEGER, 
	paid_at VARCHAR(30), 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(broker_id) REFERENCES brokers (id), 
	FOREIGN KEY(contract_id) REFERENCES contracts (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id)
)

;

-- Table: brokers

CREATE TABLE brokers (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	user_id INTEGER, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	mobile VARCHAR(50) NOT NULL, 
	email VARCHAR(255), 
	license_number VARCHAR(100), 
	commission_rate NUMERIC(5, 2) NOT NULL, 
	total_sales NUMERIC(14, 2) NOT NULL, 
	rank_score INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

-- Table: buildings

CREATE TABLE buildings (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	total_floors INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

-- Table: chart_of_accounts

CREATE TABLE chart_of_accounts (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	account_type VARCHAR(50) NOT NULL, 
	parent_id INTEGER, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(parent_id) REFERENCES chart_of_accounts (id)
)

;

-- Table: companies

CREATE TABLE companies (
	id SERIAL NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	email VARCHAR(255), 
	phone VARCHAR(50), 
	address TEXT, 
	city VARCHAR(100), 
	country VARCHAR(100) NOT NULL, 
	tax_number VARCHAR(100), 
	commercial_register VARCHAR(100), 
	logo_url VARCHAR(500), 
	status companystatus NOT NULL, 
	storage_limit_mb INTEGER NOT NULL, 
	storage_used_mb INTEGER NOT NULL, 
	default_language VARCHAR(5) NOT NULL, 
	theme VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

;

-- Table: company_subscriptions

CREATE TABLE company_subscriptions (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	start_date VARCHAR(20), 
	end_date VARCHAR(20), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (company_id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(plan_id) REFERENCES subscription_plans (id)
)

;

-- Table: construction_milestones

CREATE TABLE construction_milestones (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	target_date VARCHAR(20) NOT NULL, 
	completed_date VARCHAR(20), 
	status VARCHAR(50) NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

-- Table: construction_phases

CREATE TABLE construction_phases (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	planned_start VARCHAR(20), 
	planned_end VARCHAR(20), 
	progress_percent INTEGER NOT NULL, 
	planned_cost NUMERIC(14, 2) NOT NULL, 
	actual_cost NUMERIC(14, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

-- Table: construction_tasks

CREATE TABLE construction_tasks (
	id SERIAL NOT NULL, 
	phase_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	assigned_to_id INTEGER, 
	contractor VARCHAR(255), 
	status VARCHAR(50) NOT NULL, 
	progress_percent INTEGER NOT NULL, 
	planned_cost NUMERIC(14, 2) NOT NULL, 
	actual_cost NUMERIC(14, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(phase_id) REFERENCES construction_phases (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id)
)

;

-- Table: contracts

CREATE TABLE contracts (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	contract_number VARCHAR(50) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	reservation_id INTEGER, 
	total_price NUMERIC(14, 2) NOT NULL, 
	contract_date VARCHAR(20) NOT NULL, 
	status contractstatus NOT NULL, 
	contract_ar TEXT, 
	contract_en TEXT, 
	version INTEGER NOT NULL, 
	is_signed BOOLEAN NOT NULL, 
	signed_at VARCHAR(30), 
	approved_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (contract_number), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(reservation_id) REFERENCES reservations (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id)
)

;

-- Table: customer_activities

CREATE TABLE customer_activities (
	id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	activity_type activitytype NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	created_by_id INTEGER, 
	reference_type VARCHAR(50), 
	reference_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: customer_documents

CREATE TABLE customer_documents (
	id SERIAL NOT NULL, 
	customer_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	file_url VARCHAR(500) NOT NULL, 
	file_type VARCHAR(50), 
	uploaded_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(uploaded_by_id) REFERENCES users (id)
)

;

-- Table: customers

CREATE TABLE customers (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	user_id INTEGER, 
	full_name_ar VARCHAR(255) NOT NULL, 
	full_name_en VARCHAR(255) NOT NULL, 
	mobile VARCHAR(50) NOT NULL, 
	whatsapp VARCHAR(50), 
	email VARCHAR(255), 
	national_id VARCHAR(50), 
	passport_number VARCHAR(50), 
	address TEXT, 
	city VARCHAR(100), 
	country VARCHAR(100) NOT NULL, 
	occupation VARCHAR(255), 
	employer VARCHAR(255), 
	income_range VARCHAR(100), 
	notes TEXT, 
	assigned_to_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id)
)

;

-- Table: documents

CREATE TABLE documents (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	file_url VARCHAR(500) NOT NULL, 
	file_type VARCHAR(50), 
	category VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100), 
	entity_id INTEGER, 
	version INTEGER NOT NULL, 
	uploaded_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(uploaded_by_id) REFERENCES users (id)
)

;

-- Table: employees

CREATE TABLE employees (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	user_id INTEGER, 
	employee_code VARCHAR(50) NOT NULL, 
	full_name_ar VARCHAR(255) NOT NULL, 
	full_name_en VARCHAR(255) NOT NULL, 
	department VARCHAR(100), 
	position VARCHAR(100), 
	salary NUMERIC(12, 2), 
	hire_date VARCHAR(20), 
	manager_id INTEGER, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(manager_id) REFERENCES employees (id)
)

;

-- Table: floors

CREATE TABLE floors (
	id SERIAL NOT NULL, 
	building_id INTEGER NOT NULL, 
	floor_number INTEGER NOT NULL, 
	name_ar VARCHAR(100), 
	name_en VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(building_id) REFERENCES buildings (id)
)

;

-- Table: handover_records

CREATE TABLE handover_records (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	handover_date VARCHAR(20) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	notes TEXT, 
	completed_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(completed_by_id) REFERENCES users (id)
)

;

-- Table: installments

CREATE TABLE installments (
	id SERIAL NOT NULL, 
	payment_plan_id INTEGER NOT NULL, 
	installment_number INTEGER NOT NULL, 
	due_date VARCHAR(20) NOT NULL, 
	due_amount NUMERIC(14, 2) NOT NULL, 
	paid_amount NUMERIC(14, 2) NOT NULL, 
	remaining_balance NUMERIC(14, 2) NOT NULL, 
	status installmentstatus NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(payment_plan_id) REFERENCES payment_plans (id)
)

;

-- Table: inventory_items

CREATE TABLE inventory_items (
	id SERIAL NOT NULL, 
	warehouse_id INTEGER NOT NULL, 
	sku VARCHAR(100) NOT NULL, 
	barcode VARCHAR(100), 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	quantity NUMERIC(12, 3) NOT NULL, 
	min_stock_level NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	unit_cost NUMERIC(12, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(warehouse_id) REFERENCES warehouses (id)
)

;

-- Table: journal_entries

CREATE TABLE journal_entries (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	entry_number VARCHAR(50) NOT NULL, 
	entry_date VARCHAR(20) NOT NULL, 
	description TEXT, 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (entry_number), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: journal_lines

CREATE TABLE journal_lines (
	id SERIAL NOT NULL, 
	journal_entry_id INTEGER NOT NULL, 
	account_id INTEGER NOT NULL, 
	debit NUMERIC(14, 2) NOT NULL, 
	credit NUMERIC(14, 2) NOT NULL, 
	cost_center VARCHAR(100), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(journal_entry_id) REFERENCES journal_entries (id), 
	FOREIGN KEY(account_id) REFERENCES chart_of_accounts (id)
)

;

-- Table: lead_activities

CREATE TABLE lead_activities (
	id SERIAL NOT NULL, 
	lead_id INTEGER NOT NULL, 
	activity_type VARCHAR(50) NOT NULL, 
	description TEXT, 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lead_id) REFERENCES leads (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: leads

CREATE TABLE leads (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	customer_id INTEGER, 
	project_id INTEGER, 
	assigned_to_id INTEGER, 
	broker_id INTEGER, 
	full_name VARCHAR(255) NOT NULL, 
	mobile VARCHAR(50) NOT NULL, 
	email VARCHAR(255), 
	source leadsource NOT NULL, 
	stage leadstage NOT NULL, 
	score INTEGER NOT NULL, 
	ai_score NUMERIC(5, 2), 
	ai_qualification TEXT, 
	budget_min NUMERIC(14, 2), 
	budget_max NUMERIC(14, 2), 
	notes TEXT, 
	next_follow_up VARCHAR(30), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id), 
	FOREIGN KEY(broker_id) REFERENCES brokers (id)
)

;

-- Table: leave_requests

CREATE TABLE leave_requests (
	id SERIAL NOT NULL, 
	employee_id INTEGER NOT NULL, 
	leave_type VARCHAR(50) NOT NULL, 
	start_date VARCHAR(20) NOT NULL, 
	end_date VARCHAR(20) NOT NULL, 
	reason TEXT, 
	status VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
)

;

-- Table: maintenance_requests

CREATE TABLE maintenance_requests (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	customer_id INTEGER, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	priority VARCHAR(20) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	assigned_to_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id)
)

;

-- Table: notifications

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	company_id INTEGER, 
	user_id INTEGER NOT NULL, 
	title_ar VARCHAR(255) NOT NULL, 
	title_en VARCHAR(255) NOT NULL, 
	message_ar TEXT, 
	message_en TEXT, 
	notification_type VARCHAR(50) NOT NULL, 
	channel VARCHAR(50) NOT NULL, 
	is_read BOOLEAN NOT NULL, 
	reference_type VARCHAR(50), 
	reference_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

-- Table: payment_plans

CREATE TABLE payment_plans (
	id SERIAL NOT NULL, 
	contract_id INTEGER NOT NULL, 
	plan_type paymentplantype NOT NULL, 
	down_payment NUMERIC(14, 2) NOT NULL, 
	total_amount NUMERIC(14, 2) NOT NULL, 
	number_of_installments INTEGER NOT NULL, 
	start_date VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (contract_id), 
	FOREIGN KEY(contract_id) REFERENCES contracts (id)
)

;

-- Table: payments

CREATE TABLE payments (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	installment_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	amount NUMERIC(14, 2) NOT NULL, 
	payment_date VARCHAR(20) NOT NULL, 
	payment_method VARCHAR(50) NOT NULL, 
	reference_number VARCHAR(100), 
	received_by_id INTEGER, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(installment_id) REFERENCES installments (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(received_by_id) REFERENCES users (id)
)

;

-- Table: permissions

CREATE TABLE permissions (
	id SERIAL NOT NULL, 
	module VARCHAR(100) NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(150) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_permission_module_action UNIQUE (module, action), 
	UNIQUE (code)
)

;

-- Table: projects

CREATE TABLE projects (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	branch_id INTEGER, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	description_ar TEXT, 
	description_en TEXT, 
	city VARCHAR(100), 
	country VARCHAR(100) NOT NULL, 
	address TEXT, 
	status projectstatus NOT NULL, 
	total_units INTEGER NOT NULL, 
	available_units INTEGER NOT NULL, 
	cover_image_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id)
)

;

-- Table: purchase_orders

CREATE TABLE purchase_orders (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	po_number VARCHAR(50) NOT NULL, 
	vendor_id INTEGER NOT NULL, 
	project_id INTEGER, 
	total_amount NUMERIC(14, 2) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	approved_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (po_number), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id)
)

;

-- Table: reservations

CREATE TABLE reservations (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	reservation_number VARCHAR(50) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	deposit_amount NUMERIC(14, 2) NOT NULL, 
	reservation_date VARCHAR(20) NOT NULL, 
	expiry_date VARCHAR(20) NOT NULL, 
	status reservationstatus NOT NULL, 
	created_by_id INTEGER, 
	approved_by_id INTEGER, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (reservation_number), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id), 
	FOREIGN KEY(approved_by_id) REFERENCES users (id)
)

;

-- Table: rfqs

CREATE TABLE rfqs (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	rfq_number VARCHAR(50) NOT NULL, 
	project_id INTEGER, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(50) NOT NULL, 
	due_date VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (rfq_number), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;

-- Table: role_permissions

CREATE TABLE role_permissions (
	id SERIAL NOT NULL, 
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(permission_id) REFERENCES permissions (id)
)

;

-- Table: roles

CREATE TABLE roles (
	id SERIAL NOT NULL, 
	company_id INTEGER, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(100) NOT NULL, 
	description TEXT, 
	is_system BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
)

;

-- Table: stock_movements

CREATE TABLE stock_movements (
	id SERIAL NOT NULL, 
	item_id INTEGER NOT NULL, 
	movement_type VARCHAR(50) NOT NULL, 
	quantity NUMERIC(12, 3) NOT NULL, 
	from_warehouse_id INTEGER, 
	to_warehouse_id INTEGER, 
	reference VARCHAR(100), 
	created_by_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_id) REFERENCES inventory_items (id), 
	FOREIGN KEY(from_warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(to_warehouse_id) REFERENCES warehouses (id), 
	FOREIGN KEY(created_by_id) REFERENCES users (id)
)

;

-- Table: subscription_plans

CREATE TABLE subscription_plans (
	id SERIAL NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	price_monthly NUMERIC(12, 2) NOT NULL, 
	price_yearly NUMERIC(12, 2) NOT NULL, 
	max_users INTEGER NOT NULL, 
	max_projects INTEGER NOT NULL, 
	max_storage_mb INTEGER NOT NULL, 
	features TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

-- Table: system_settings

CREATE TABLE system_settings (
	id SERIAL NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	value TEXT, 
	value_type VARCHAR(20) NOT NULL, 
	description_ar TEXT, 
	description_en TEXT, 
	is_public BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (key)
)

;

-- Table: ticket_comments

CREATE TABLE ticket_comments (
	id SERIAL NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	comment TEXT NOT NULL, 
	is_internal BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES tickets (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

-- Table: tickets

CREATE TABLE tickets (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	ticket_number VARCHAR(50) NOT NULL, 
	customer_id INTEGER, 
	category VARCHAR(100) NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	description TEXT, 
	priority VARCHAR(20) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	assigned_to_id INTEGER, 
	sla_due_at VARCHAR(30), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	UNIQUE (ticket_number), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id)
)

;

-- Table: units

CREATE TABLE units (
	id SERIAL NOT NULL, 
	floor_id INTEGER NOT NULL, 
	unit_code VARCHAR(50) NOT NULL, 
	unit_number VARCHAR(50) NOT NULL, 
	unit_type unittype NOT NULL, 
	area_sqm NUMERIC(10, 2) NOT NULL, 
	garden_area_sqm NUMERIC(10, 2), 
	roof_area_sqm NUMERIC(10, 2), 
	bedrooms INTEGER NOT NULL, 
	bathrooms INTEGER NOT NULL, 
	price NUMERIC(14, 2) NOT NULL, 
	maintenance_fee NUMERIC(12, 2), 
	delivery_date VARCHAR(20), 
	status unitstatus NOT NULL, 
	images TEXT, 
	attachments TEXT, 
	is_locked BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(floor_id) REFERENCES floors (id)
)

;

-- Table: user_roles

CREATE TABLE user_roles (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
)

;

-- Table: users

CREATE TABLE users (
	id SERIAL NOT NULL, 
	company_id INTEGER, 
	branch_id INTEGER, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name_ar VARCHAR(255) NOT NULL, 
	full_name_en VARCHAR(255) NOT NULL, 
	phone VARCHAR(50), 
	avatar_url VARCHAR(500), 
	system_role systemrole NOT NULL, 
	status userstatus NOT NULL, 
	is_super_admin BOOLEAN NOT NULL, 
	preferred_language VARCHAR(5) NOT NULL, 
	totp_secret VARCHAR(64), 
	is_2fa_enabled BOOLEAN NOT NULL, 
	last_login_at VARCHAR(50), 
	last_login_ip VARCHAR(50), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	is_deleted BOOLEAN NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id)
)

;

-- Table: vendors

CREATE TABLE vendors (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	contact_person VARCHAR(255), 
	phone VARCHAR(50), 
	email VARCHAR(255), 
	rating INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
)

;

-- Table: warehouses

CREATE TABLE warehouses (
	id SERIAL NOT NULL, 
	company_id INTEGER NOT NULL, 
	name_ar VARCHAR(255) NOT NULL, 
	name_en VARCHAR(255) NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	location VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
)

;
