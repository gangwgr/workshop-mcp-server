# RoverPeople Data Product - LLM Guidance

## 🚨 CRITICAL: RHEL Organization Search Rule
**WHEN SEARCHING FOR RHEL ORGANIZATION**, clarify the intent:

### For MAIN RHEL Team Only (~1,614 employees):
- ✅ Use: `product_alignment = 'Red Hat Enterprise Linux'`
- This captures the core RHEL product team

### For ALL RHEL-Related Teams (~1,691 total employees):
- ✅ Use: `(product_alignment LIKE '%Red Hat Enterprise Linux%' OR product_alignment LIKE '%RHEL%')`
- This includes main team + specialized variants (RHEL for Edge, RHEL AI, etc.)

### Common Mistake:
- ❌ Using only `product_alignment LIKE '%RHEL%'` misses the main team and returns only ~75 employees from sub-teams

## Quick Overview
RoverPeople is Red Hat's internal corporate directory with employee and contractor information. Use the `marts` schema for all queries.

## Primary Tables

### `roverpeople_db.marts.rover_people_curr` - Active Employees
- **Key**: `uuid` (primary key), `employee_number`
- **Filters**: Active only (`term_date IS NULL`, `former_employee = 'false'`)
- **Records**: Contains all active employees and contractors
- **Core Fields**: display_name, mail, job_role, manager_uuid, cost_center, hire_date, geo

### `roverpeople_db.marts.rover_alignment_curr` - Employee Alignments
- **Purpose**: Complete employee profile with product/project/role alignments
- **Records**: Subset of employees with product/project alignments
- **Key Fields**: uuid, product_alignment, project_alignment, role_alignment, subproduct_alignment
- **Note**: Joins all alignment types to people data

## Critical Data Quality Notes

### Job Role Coverage
```sql
-- WARNING: Many job_role fields are NULL
-- Use role_alignment instead for better coverage
WHERE role_alignment = 'Engineering'  -- More reliable than job_role
```

### Geographic Data
- **Country**: Not populated (shows "Not Specified")
- **Use `geo`**: Returns regional values (NA, EMEA, APAC, LATAM)

### Manager Hierarchy
- **Coverage**: All records have manager_uuid populated
- **Self-join pattern**: `JOIN roverpeople_db.marts.rover_people_curr m ON e.manager_uuid = m.uuid`

## Essential Query Patterns

### Employee Lookup
```sql
-- Find by email
SELECT uuid, display_name, job_role, organization, cost_center
FROM roverpeople_db.marts.rover_people_curr
WHERE mail = 'user@redhat.com';

-- Get with alignments
SELECT p.*, a.product_alignment, a.role_alignment
FROM roverpeople_db.marts.rover_people_curr p
LEFT JOIN roverpeople_db.marts.rover_alignment_curr a ON p.uuid = a.uuid
WHERE p.mail = 'user@redhat.com';
```

### Team Analysis
```sql
-- Product team sizes
SELECT
    p.cost_center_desc,
    COUNT(*) as employee_count
FROM roverpeople_db.marts.rover_people_curr p
JOIN roverpeople_db.marts.rover_alignment_curr a ON p.uuid = a.uuid
WHERE a.product_alignment LIKE '%[Product Name]%'
GROUP BY p.cost_center_desc
ORDER BY employee_count DESC;
```

### Organizational Structure
```sql
-- Manager's team
SELECT
    e.display_name as employee,
    e.mail,
    e.job_role
FROM roverpeople_db.marts.rover_people_curr e
WHERE e.manager_uuid = (
    SELECT uuid FROM roverpeople_db.marts.rover_people_curr
    WHERE mail = 'manager@redhat.com'
);

-- Cost center breakdown
SELECT
    cost_center_desc,
    COUNT(*) as headcount,
    COUNT(CASE WHEN employee_type = 'Employee' THEN 1 END) as employees,
    COUNT(CASE WHEN employee_type = 'Contingent Worker' THEN 1 END) as contractors
FROM roverpeople_db.marts.rover_people_curr
GROUP BY cost_center_desc
ORDER BY headcount DESC;
```

### Tenure Analysis
```sql
-- Hiring trends
SELECT
    YEAR(hire_date) as hire_year,
    COUNT(*) as hires,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as percentage
FROM roverpeople_db.marts.rover_people_curr
WHERE hire_date IS NOT NULL
GROUP BY YEAR(hire_date)
ORDER BY hire_year DESC;
```

## Key Business Insights

### Product Alignment Patterns
- **Coverage**: Not all employees have product alignments
- **Multi-Product**: Some employees have multiple alignments (comma-separated)
- **Common Products**: Major products include Red Hat Enterprise Linux, OpenShift, Ansible, and others
- **RHEL Teams Structure**:
  - Main team: "Red Hat Enterprise Linux" (~1,614 employees)
  - Specialized variants: "RHEL for Edge", "Red Hat Enterprise Linux AI", etc. (~77 additional)
  - Total RHEL ecosystem: ~1,691 employees across all RHEL-related teams

### Data Characteristics
- **Employee Types**: Mix of employees and contractors
- **Geographic Distribution**: Covers all major regions (NA, EMEA, APAC, LATAM)
- **Manager Hierarchy**: Complete manager relationships available

### Organization Structure
- **Cost Centers**: Multiple R&D, Support, Marketing, and other functional areas
- **Alignment Types**: Product, Project, Role, and Subproduct alignments available

## Query Strategy

### For Complete Workforce
```sql
-- Use rover_people_curr for all employees
SELECT * FROM roverpeople_db.marts.rover_people_curr
WHERE term_date IS NULL;  -- Active only
```

### For Product Teams
```sql
-- Use rover_alignment_curr for employees with assignments
SELECT * FROM roverpeople_db.marts.rover_alignment_curr
WHERE product_alignment IS NOT NULL;
```

### Product Search Best Practices
**RHEL Organization Searches**: Be specific about which teams you want
```sql
-- For MAIN RHEL team only (~1,614 employees):
WHERE product_alignment = 'Red Hat Enterprise Linux'

-- For ALL RHEL-related teams (~1,691 employees):
WHERE (product_alignment LIKE '%Red Hat Enterprise Linux%'
       OR product_alignment LIKE '%RHEL%')

-- INCORRECT: This misses the main team (~75 employees only)
WHERE product_alignment LIKE '%RHEL%'

-- Example: Get all RHEL-related teams with breakdown
SELECT
    product_alignment,
    COUNT(*) as employee_count
FROM roverpeople_db.marts.rover_alignment_curr
WHERE (product_alignment LIKE '%Red Hat Enterprise Linux%'
       OR product_alignment LIKE '%RHEL%')
GROUP BY product_alignment
ORDER BY employee_count DESC;
```

### Performance Tips
- Filter early with WHERE clauses
- Use specific product names in LIKE clauses
- Join on uuid for best performance

## Data Freshness & Limitations

- **Update Frequency**: Daily
- **Change Tracking**: Use `_fivetran_synced` timestamp
- **Historical Data**: Terminated employees have `term_date` populated
- **Real-time**: Not suitable for real-time applications

## Common Pitfalls to Avoid

1. **Don't assume job_role is populated** - High NULL rate
2. **Don't use country field** - Use geo instead
3. **Don't expect all employees in alignments** - Partial coverage only
4. **Don't query staging tables** - Use marts schema only
5. **Be specific with RHEL searches** - Use "Red Hat Enterprise Linux" for main team only, or combine with OR for all RHEL-related teams

## Quick Reference

| Table | Purpose | Key Filter |
|-------|---------|------------|
| roverpeople_db.marts.rover_people_curr | All active employees | term_date IS NULL |
| roverpeople_db.marts.rover_alignment_curr | Employees with alignments | Has product/role alignment |
| roverpeople_db.marts.rover_product_curr | Product alignments | By uuid |
| roverpeople_db.marts.rover_role_curr | Role alignments | By uuid |

## Security Note
Contains confidential employee data. Use aggregate queries when possible and follow principle of least privilege.
