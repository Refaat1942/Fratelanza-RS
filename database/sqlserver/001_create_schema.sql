/*
Fratelanza Business Suite - SQL Server bootstrap schema

This script is idempotent for first deployment and creates the database plus the
core schemas required by the desktop application. Replace __DATABASE_NAME__ at
runtime through SchemaManager or manually before executing in SSMS.
*/

DECLARE @DatabaseName sysname = N'__DATABASE_NAME__';
IF DB_ID(@DatabaseName) IS NULL
BEGIN
    DECLARE @CreateDatabaseSql nvarchar(max) = N'CREATE DATABASE ' + QUOTENAME(@DatabaseName);
    EXEC sys.sp_executesql @CreateDatabaseSql;
END;
GO

USE [__DATABASE_NAME__];
GO

CREATE SCHEMA security;
GO
CREATE SCHEMA crm;
GO
CREATE SCHEMA inventory;
GO
CREATE SCHEMA sales;
GO
CREATE SCHEMA finance;
GO
CREATE SCHEMA settings;
GO
CREATE SCHEMA reporting;
GO
CREATE SCHEMA notifications;
GO
CREATE SCHEMA audit;
GO
CREATE SCHEMA system;
GO

CREATE TABLE security.Roles (
    RoleId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Roles PRIMARY KEY,
    RoleName nvarchar(80) NOT NULL CONSTRAINT UQ_Roles_RoleName UNIQUE,
    Description nvarchar(255) NULL,
    IsSystemRole bit NOT NULL CONSTRAINT DF_Roles_IsSystemRole DEFAULT 0,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Roles_CreatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE security.Permissions (
    PermissionId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Permissions PRIMARY KEY,
    PermissionKey nvarchar(120) NOT NULL CONSTRAINT UQ_Permissions_Key UNIQUE,
    Description nvarchar(255) NULL
);

CREATE TABLE security.RolePermissions (
    RoleId int NOT NULL,
    PermissionId int NOT NULL,
    CONSTRAINT PK_RolePermissions PRIMARY KEY (RoleId, PermissionId),
    CONSTRAINT FK_RolePermissions_Roles FOREIGN KEY (RoleId) REFERENCES security.Roles(RoleId),
    CONSTRAINT FK_RolePermissions_Permissions FOREIGN KEY (PermissionId) REFERENCES security.Permissions(PermissionId)
);

CREATE TABLE security.Users (
    UserId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Users PRIMARY KEY,
    RoleId int NOT NULL,
    Username nvarchar(80) NOT NULL CONSTRAINT UQ_Users_Username UNIQUE,
    DisplayName nvarchar(160) NOT NULL,
    Email nvarchar(160) NULL,
    PasswordHash nvarchar(512) NOT NULL,
    IsActive bit NOT NULL CONSTRAINT DF_Users_IsActive DEFAULT 1,
    LastLoginAt datetime2(0) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Users_CreatedAt DEFAULT sysutcdatetime(),
    UpdatedAt datetime2(0) NULL,
    CONSTRAINT FK_Users_Roles FOREIGN KEY (RoleId) REFERENCES security.Roles(RoleId)
);

CREATE TABLE security.UserActivityLogs (
    ActivityLogId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_UserActivityLogs PRIMARY KEY,
    UserId int NULL,
    ActivityType nvarchar(80) NOT NULL,
    Description nvarchar(500) NOT NULL,
    IpAddress nvarchar(64) NULL,
    DeviceName nvarchar(160) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_UserActivityLogs_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_UserActivityLogs_Users FOREIGN KEY (UserId) REFERENCES security.Users(UserId)
);

CREATE TABLE crm.Customers (
    CustomerId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Customers PRIMARY KEY,
    CustomerCode nvarchar(40) NOT NULL CONSTRAINT UQ_Customers_Code UNIQUE,
    FullName nvarchar(180) NOT NULL,
    Phone nvarchar(40) NULL,
    Email nvarchar(160) NULL,
    AddressLine nvarchar(300) NULL,
    TaxNumber nvarchar(80) NULL,
    CreditLimit decimal(18,2) NOT NULL CONSTRAINT DF_Customers_CreditLimit DEFAULT 0,
    OpeningBalance decimal(18,2) NOT NULL CONSTRAINT DF_Customers_OpeningBalance DEFAULT 0,
    IsActive bit NOT NULL CONSTRAINT DF_Customers_IsActive DEFAULT 1,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Customers_CreatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE crm.Suppliers (
    SupplierId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Suppliers PRIMARY KEY,
    SupplierCode nvarchar(40) NOT NULL CONSTRAINT UQ_Suppliers_Code UNIQUE,
    SupplierName nvarchar(180) NOT NULL,
    ContactPerson nvarchar(160) NULL,
    Phone nvarchar(40) NULL,
    Email nvarchar(160) NULL,
    AddressLine nvarchar(300) NULL,
    TaxNumber nvarchar(80) NULL,
    OpeningBalance decimal(18,2) NOT NULL CONSTRAINT DF_Suppliers_OpeningBalance DEFAULT 0,
    IsActive bit NOT NULL CONSTRAINT DF_Suppliers_IsActive DEFAULT 1,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Suppliers_CreatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE inventory.Categories (
    CategoryId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Categories PRIMARY KEY,
    ParentCategoryId int NULL,
    CategoryName nvarchar(140) NOT NULL,
    Description nvarchar(255) NULL,
    IsActive bit NOT NULL CONSTRAINT DF_Categories_IsActive DEFAULT 1,
    CONSTRAINT FK_Categories_Parent FOREIGN KEY (ParentCategoryId) REFERENCES inventory.Categories(CategoryId)
);

CREATE TABLE inventory.Brands (
    BrandId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Brands PRIMARY KEY,
    BrandName nvarchar(140) NOT NULL CONSTRAINT UQ_Brands_Name UNIQUE,
    IsActive bit NOT NULL CONSTRAINT DF_Brands_IsActive DEFAULT 1
);

CREATE TABLE inventory.Units (
    UnitId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Units PRIMARY KEY,
    UnitName nvarchar(80) NOT NULL CONSTRAINT UQ_Units_Name UNIQUE,
    Symbol nvarchar(20) NOT NULL,
    AllowsDecimals bit NOT NULL CONSTRAINT DF_Units_AllowsDecimals DEFAULT 0
);

CREATE TABLE inventory.Products (
    ProductId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Products PRIMARY KEY,
    CategoryId int NOT NULL,
    BrandId int NULL,
    UnitId int NOT NULL,
    Sku nvarchar(60) NOT NULL CONSTRAINT UQ_Products_Sku UNIQUE,
    ProductName nvarchar(220) NOT NULL,
    ProductCode nvarchar(80) NOT NULL CONSTRAINT UQ_Products_ProductCode UNIQUE,
    Barcode nvarchar(80) NULL CONSTRAINT UQ_Products_Barcode UNIQUE,
    Description nvarchar(500) NULL,
    CostPrice decimal(18,4) NOT NULL CONSTRAINT DF_Products_CostPrice DEFAULT 0,
    SalePrice decimal(18,4) NOT NULL CONSTRAINT DF_Products_SalePrice DEFAULT 0,
    TaxRate decimal(9,4) NOT NULL CONSTRAINT DF_Products_TaxRate DEFAULT 0,
    QuantityOnHand decimal(18,4) NOT NULL CONSTRAINT DF_Products_QuantityOnHand DEFAULT 0,
    ReorderLevel decimal(18,4) NOT NULL CONSTRAINT DF_Products_ReorderLevel DEFAULT 0,
    ExpiryDate date NULL,
    IsActive bit NOT NULL CONSTRAINT DF_Products_IsActive DEFAULT 1,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Products_CreatedAt DEFAULT sysutcdatetime(),
    UpdatedAt datetime2(0) NULL,
    CONSTRAINT FK_Products_Categories FOREIGN KEY (CategoryId) REFERENCES inventory.Categories(CategoryId),
    CONSTRAINT FK_Products_Brands FOREIGN KEY (BrandId) REFERENCES inventory.Brands(BrandId),
    CONSTRAINT FK_Products_Units FOREIGN KEY (UnitId) REFERENCES inventory.Units(UnitId)
);

CREATE INDEX IX_Products_Search ON inventory.Products(ProductName, Sku, Barcode);

CREATE TABLE inventory.StockMovements (
    StockMovementId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_StockMovements PRIMARY KEY,
    ProductId int NOT NULL,
    MovementType nvarchar(40) NOT NULL,
    Quantity decimal(18,4) NOT NULL,
    UnitCost decimal(18,4) NULL,
    ReferenceType nvarchar(60) NULL,
    ReferenceId bigint NULL,
    Notes nvarchar(500) NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_StockMovements_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_StockMovements_Products FOREIGN KEY (ProductId) REFERENCES inventory.Products(ProductId),
    CONSTRAINT FK_StockMovements_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE sales.SalesInvoices (
    SalesInvoiceId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesInvoices PRIMARY KEY,
    InvoiceNumber nvarchar(60) NOT NULL CONSTRAINT UQ_SalesInvoices_Number UNIQUE,
    CustomerId int NULL,
    InvoiceStatus nvarchar(40) NOT NULL CONSTRAINT DF_SalesInvoices_Status DEFAULT N'draft',
    Subtotal decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoices_Subtotal DEFAULT 0,
    DiscountTotal decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoices_DiscountTotal DEFAULT 0,
    TaxTotal decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoices_TaxTotal DEFAULT 0,
    GrandTotal decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoices_GrandTotal DEFAULT 0,
    PaidTotal decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoices_PaidTotal DEFAULT 0,
    Notes nvarchar(500) NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_SalesInvoices_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_SalesInvoices_Customers FOREIGN KEY (CustomerId) REFERENCES crm.Customers(CustomerId),
    CONSTRAINT FK_SalesInvoices_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE sales.SalesInvoiceItems (
    SalesInvoiceItemId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesInvoiceItems PRIMARY KEY,
    SalesInvoiceId bigint NOT NULL,
    ProductId int NOT NULL,
    Quantity decimal(18,4) NOT NULL,
    UnitPrice decimal(18,4) NOT NULL,
    DiscountAmount decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoiceItems_Discount DEFAULT 0,
    TaxAmount decimal(18,2) NOT NULL CONSTRAINT DF_SalesInvoiceItems_Tax DEFAULT 0,
    LineTotal decimal(18,2) NOT NULL,
    CONSTRAINT FK_SalesInvoiceItems_Invoices FOREIGN KEY (SalesInvoiceId) REFERENCES sales.SalesInvoices(SalesInvoiceId),
    CONSTRAINT FK_SalesInvoiceItems_Products FOREIGN KEY (ProductId) REFERENCES inventory.Products(ProductId)
);

CREATE TABLE sales.SalesPayments (
    SalesPaymentId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesPayments PRIMARY KEY,
    SalesInvoiceId bigint NOT NULL,
    PaymentMethod nvarchar(40) NOT NULL,
    Amount decimal(18,2) NOT NULL,
    ReferenceNumber nvarchar(120) NULL,
    PaidAt datetime2(0) NOT NULL CONSTRAINT DF_SalesPayments_PaidAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_SalesPayments_Invoices FOREIGN KEY (SalesInvoiceId) REFERENCES sales.SalesInvoices(SalesInvoiceId)
);

CREATE TABLE sales.SalesReturns (
    SalesReturnId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesReturns PRIMARY KEY,
    SalesInvoiceId bigint NOT NULL,
    ReturnNumber nvarchar(60) NOT NULL CONSTRAINT UQ_SalesReturns_Number UNIQUE,
    Reason nvarchar(500) NULL,
    TotalAmount decimal(18,2) NOT NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_SalesReturns_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_SalesReturns_Invoices FOREIGN KEY (SalesInvoiceId) REFERENCES sales.SalesInvoices(SalesInvoiceId),
    CONSTRAINT FK_SalesReturns_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE sales.SalesReturnItems (
    SalesReturnItemId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SalesReturnItems PRIMARY KEY,
    SalesReturnId bigint NOT NULL,
    ProductId int NOT NULL,
    Quantity decimal(18,4) NOT NULL,
    UnitPrice decimal(18,4) NOT NULL,
    LineTotal decimal(18,2) NOT NULL,
    CONSTRAINT FK_SalesReturnItems_Returns FOREIGN KEY (SalesReturnId) REFERENCES sales.SalesReturns(SalesReturnId),
    CONSTRAINT FK_SalesReturnItems_Products FOREIGN KEY (ProductId) REFERENCES inventory.Products(ProductId)
);

CREATE TABLE finance.Cashboxes (
    CashboxId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_Cashboxes PRIMARY KEY,
    CashboxName nvarchar(120) NOT NULL CONSTRAINT UQ_Cashboxes_Name UNIQUE,
    OpeningBalance decimal(18,2) NOT NULL CONSTRAINT DF_Cashboxes_OpeningBalance DEFAULT 0,
    CurrentBalance decimal(18,2) NOT NULL CONSTRAINT DF_Cashboxes_CurrentBalance DEFAULT 0,
    IsActive bit NOT NULL CONSTRAINT DF_Cashboxes_IsActive DEFAULT 1
);

CREATE TABLE finance.ExpenseCategories (
    ExpenseCategoryId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_ExpenseCategories PRIMARY KEY,
    CategoryName nvarchar(140) NOT NULL CONSTRAINT UQ_ExpenseCategories_Name UNIQUE
);

CREATE TABLE finance.Expenses (
    ExpenseId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Expenses PRIMARY KEY,
    ExpenseCategoryId int NOT NULL,
    CashboxId int NULL,
    Amount decimal(18,2) NOT NULL,
    ExpenseDate date NOT NULL,
    Description nvarchar(500) NOT NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Expenses_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_Expenses_Categories FOREIGN KEY (ExpenseCategoryId) REFERENCES finance.ExpenseCategories(ExpenseCategoryId),
    CONSTRAINT FK_Expenses_Cashboxes FOREIGN KEY (CashboxId) REFERENCES finance.Cashboxes(CashboxId),
    CONSTRAINT FK_Expenses_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE finance.Revenues (
    RevenueId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Revenues PRIMARY KEY,
    CashboxId int NULL,
    Amount decimal(18,2) NOT NULL,
    RevenueDate date NOT NULL,
    SourceName nvarchar(160) NOT NULL,
    Description nvarchar(500) NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Revenues_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_Revenues_Cashboxes FOREIGN KEY (CashboxId) REFERENCES finance.Cashboxes(CashboxId),
    CONSTRAINT FK_Revenues_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE finance.CashboxTransactions (
    CashboxTransactionId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_CashboxTransactions PRIMARY KEY,
    CashboxId int NOT NULL,
    TransactionType nvarchar(40) NOT NULL,
    Amount decimal(18,2) NOT NULL,
    ReferenceType nvarchar(60) NULL,
    ReferenceId bigint NULL,
    Description nvarchar(500) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_CashboxTransactions_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_CashboxTransactions_Cashboxes FOREIGN KEY (CashboxId) REFERENCES finance.Cashboxes(CashboxId)
);

CREATE TABLE finance.CustomerAccountTransactions (
    CustomerAccountTransactionId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_CustomerAccountTransactions PRIMARY KEY,
    CustomerId int NOT NULL,
    TransactionType nvarchar(40) NOT NULL,
    Debit decimal(18,2) NOT NULL CONSTRAINT DF_CustomerAccountTransactions_Debit DEFAULT 0,
    Credit decimal(18,2) NOT NULL CONSTRAINT DF_CustomerAccountTransactions_Credit DEFAULT 0,
    ReferenceType nvarchar(60) NULL,
    ReferenceId bigint NULL,
    Description nvarchar(500) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_CustomerAccountTransactions_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_CustomerAccountTransactions_Customers FOREIGN KEY (CustomerId) REFERENCES crm.Customers(CustomerId)
);

CREATE TABLE finance.SupplierAccountTransactions (
    SupplierAccountTransactionId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_SupplierAccountTransactions PRIMARY KEY,
    SupplierId int NOT NULL,
    TransactionType nvarchar(40) NOT NULL,
    Debit decimal(18,2) NOT NULL CONSTRAINT DF_SupplierAccountTransactions_Debit DEFAULT 0,
    Credit decimal(18,2) NOT NULL CONSTRAINT DF_SupplierAccountTransactions_Credit DEFAULT 0,
    ReferenceType nvarchar(60) NULL,
    ReferenceId bigint NULL,
    Description nvarchar(500) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_SupplierAccountTransactions_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_SupplierAccountTransactions_Suppliers FOREIGN KEY (SupplierId) REFERENCES crm.Suppliers(SupplierId)
);

CREATE TABLE settings.CompanyProfile (
    CompanyProfileId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_CompanyProfile PRIMARY KEY,
    CompanyName nvarchar(180) NOT NULL,
    TradeName nvarchar(180) NULL,
    TaxNumber nvarchar(80) NULL,
    Phone nvarchar(40) NULL,
    Email nvarchar(160) NULL,
    AddressLine nvarchar(300) NULL,
    LogoPath nvarchar(260) NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_CompanyProfile_UpdatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE settings.TaxSettings (
    TaxSettingId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_TaxSettings PRIMARY KEY,
    TaxName nvarchar(80) NOT NULL,
    TaxRate decimal(9,4) NOT NULL,
    IsDefault bit NOT NULL CONSTRAINT DF_TaxSettings_IsDefault DEFAULT 0,
    IsActive bit NOT NULL CONSTRAINT DF_TaxSettings_IsActive DEFAULT 1
);

CREATE TABLE settings.CurrencySettings (
    CurrencyCode nchar(3) NOT NULL CONSTRAINT PK_CurrencySettings PRIMARY KEY,
    CurrencyName nvarchar(80) NOT NULL,
    Symbol nvarchar(10) NOT NULL,
    DecimalPlaces tinyint NOT NULL CONSTRAINT DF_CurrencySettings_DecimalPlaces DEFAULT 2,
    IsDefault bit NOT NULL CONSTRAINT DF_CurrencySettings_IsDefault DEFAULT 0
);

CREATE TABLE settings.ApplicationSettings (
    SettingKey nvarchar(120) NOT NULL CONSTRAINT PK_ApplicationSettings PRIMARY KEY,
    SettingValue nvarchar(max) NOT NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_ApplicationSettings_UpdatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE settings.ClientBranding (
    ClientBrandingId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_ClientBranding PRIMARY KEY,
    ClientDisplayName nvarchar(180) NOT NULL,
    LogoPath nvarchar(500) NULL,
    PrimaryColor nvarchar(20) NOT NULL CONSTRAINT DF_ClientBranding_PrimaryColor DEFAULT N'#55d6be',
    PreferredLocale nvarchar(10) NOT NULL CONSTRAINT DF_ClientBranding_PreferredLocale DEFAULT N'en',
    ThemeName nvarchar(40) NOT NULL CONSTRAINT DF_ClientBranding_ThemeName DEFAULT N'dark',
    IsActive bit NOT NULL CONSTRAINT DF_ClientBranding_IsActive DEFAULT 1,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_ClientBranding_UpdatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE reporting.SavedReports (
    SavedReportId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_SavedReports PRIMARY KEY,
    ReportKey nvarchar(120) NOT NULL,
    ReportName nvarchar(180) NOT NULL,
    ParametersJson nvarchar(max) NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_SavedReports_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_SavedReports_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE notifications.Notifications (
    NotificationId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Notifications PRIMARY KEY,
    UserId int NULL,
    Title nvarchar(160) NOT NULL,
    Message nvarchar(500) NOT NULL,
    Severity nvarchar(30) NOT NULL CONSTRAINT DF_Notifications_Severity DEFAULT N'info',
    IsRead bit NOT NULL CONSTRAINT DF_Notifications_IsRead DEFAULT 0,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_Notifications_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_Notifications_Users FOREIGN KEY (UserId) REFERENCES security.Users(UserId)
);

CREATE TABLE audit.EntityAuditLogs (
    EntityAuditLogId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_EntityAuditLogs PRIMARY KEY,
    EntityName nvarchar(120) NOT NULL,
    EntityId nvarchar(80) NOT NULL,
    ActionName nvarchar(40) NOT NULL,
    BeforeJson nvarchar(max) NULL,
    AfterJson nvarchar(max) NULL,
    CreatedByUserId int NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_EntityAuditLogs_CreatedAt DEFAULT sysutcdatetime(),
    CONSTRAINT FK_EntityAuditLogs_Users FOREIGN KEY (CreatedByUserId) REFERENCES security.Users(UserId)
);

CREATE TABLE system.BackupHistory (
    BackupHistoryId bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_BackupHistory PRIMARY KEY,
    BackupPath nvarchar(500) NOT NULL,
    BackupType nvarchar(40) NOT NULL,
    Status nvarchar(40) NOT NULL,
    ErrorMessage nvarchar(1000) NULL,
    CreatedAt datetime2(0) NOT NULL CONSTRAINT DF_BackupHistory_CreatedAt DEFAULT sysutcdatetime()
);

CREATE TABLE system.RemoteControlState (
    RemoteControlStateId int IDENTITY(1,1) NOT NULL CONSTRAINT PK_RemoteControlState PRIMARY KEY,
    ClientId nvarchar(120) NULL,
    InstallationId nvarchar(120) NULL,
    ApiBaseUrl nvarchar(500) NULL,
    LicenseState nvarchar(40) NOT NULL CONSTRAINT DF_RemoteControlState_LicenseState DEFAULT N'not_configured',
    AllowRemoteSupport bit NOT NULL CONSTRAINT DF_RemoteControlState_AllowSupport DEFAULT 0,
    AllowRemoteDisable bit NOT NULL CONSTRAINT DF_RemoteControlState_AllowDisable DEFAULT 1,
    LastHeartbeatAt datetime2(0) NULL,
    LastMessage nvarchar(1000) NULL,
    UpdatedAt datetime2(0) NOT NULL CONSTRAINT DF_RemoteControlState_UpdatedAt DEFAULT sysutcdatetime()
);

INSERT INTO security.Roles (RoleName, Description, IsSystemRole)
VALUES
    (N'Admin', N'Full system administrator', 1),
    (N'Manager', N'Business manager with broad operational access', 1),
    (N'Cashier', N'Sales and customer service user', 1),
    (N'Inventory Clerk', N'Inventory and barcode management user', 1),
    (N'Accountant', N'Finance and reporting user', 1);

INSERT INTO security.Permissions (PermissionKey, Description)
VALUES
    (N'dashboard.view', N'View dashboard'),
    (N'users.manage', N'Manage users and roles'),
    (N'sales.view', N'View sales'),
    (N'sales.create', N'Create sales invoices'),
    (N'sales.return', N'Create sales returns'),
    (N'inventory.view', N'View inventory'),
    (N'inventory.manage', N'Manage inventory'),
    (N'finance.view', N'View finance'),
    (N'finance.manage', N'Manage finance'),
    (N'crm.view', N'View customers and suppliers'),
    (N'crm.manage', N'Manage customers and suppliers'),
    (N'reports.view', N'View reports'),
    (N'settings.manage', N'Manage system settings'),
    (N'barcode.manage', N'Manage barcode labels'),
    (N'admin_panel.manage', N'Manage VPS control, licensing, and branding');

INSERT INTO security.RolePermissions (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM security.Roles r
CROSS JOIN security.Permissions p
WHERE r.RoleName = N'Admin';

INSERT INTO security.Users (RoleId, Username, DisplayName, Email, PasswordHash)
SELECT RoleId, N'admin', N'Fratelanza Administrator', N'admin@fratelanza.local',
       N'pbkdf2_sha256$390000$dXwyKHNWpURBZ9MoXJ1WlA==$7JBV5bpMIdriEeEJFd9GE6Mw2MihEPvM+fw+HStPxrU='
FROM security.Roles
WHERE RoleName = N'Admin';

INSERT INTO inventory.Categories (CategoryName, Description)
VALUES (N'General', N'Default product category');

INSERT INTO inventory.Units (UnitName, Symbol, AllowsDecimals)
VALUES (N'Piece', N'pc', 0), (N'Box', N'box', 0), (N'Kilogram', N'kg', 1);

INSERT INTO finance.Cashboxes (CashboxName)
VALUES (N'Main Cashbox');

INSERT INTO settings.CompanyProfile (CompanyName, TradeName)
VALUES (N'Fratelanza Client Company', N'Fratelanza');

INSERT INTO settings.CurrencySettings (CurrencyCode, CurrencyName, Symbol, DecimalPlaces, IsDefault)
VALUES (N'USD', N'US Dollar', N'$', 2, 1);

INSERT INTO settings.ApplicationSettings (SettingKey, SettingValue)
VALUES
    (N'theme', N'dark'),
    (N'barcode.prefix', N'FRA'),
    (N'backup.enabled', N'true');

INSERT INTO settings.ClientBranding (ClientDisplayName, PreferredLocale, ThemeName)
VALUES (N'Fratelanza Client Company', N'en', N'dark');

INSERT INTO system.RemoteControlState (LicenseState, LastMessage)
VALUES (N'not_configured', N'VPS control is not configured.');
