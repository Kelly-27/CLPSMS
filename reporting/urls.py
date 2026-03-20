from django.urls import path
from django.shortcuts import render
from .views import (reporting_desk, view_officers, delete_officer, report_case, generate_case_pdf, view_cases,
                    officer_dashboard, close_case, delete_case, book_suspect, view_inmates, update_inmate_status,
                    police_commander_dashboard, add_evidence, view_evidence, view_inventory, add_inventory_item,
                    update_inventory_item, view_rosters, add_roster, system_audit_logs, evidence_chain_of_custody,
                    create_charge_sheet)

urlpatterns = [
    path('reporting-desk/', reporting_desk, name='reporting_desk'),
    path('report-case/', report_case, name='report_case'),
    path('view-evidence/', view_evidence, name='view_evidence'),
    path('add-evidence/', add_evidence, name='add_evidence'),
    path('view-inmates/', view_inmates, name='view_inmates'),
    path('view-cases/', view_cases, name='view_cases'),
    path('view-officers/', view_officers, name='view_officers'),
    path('delete-officer/<int:user_id>/', delete_officer, name='delete_officer'),
    path('case/<int:case_id>/pdf/', generate_case_pdf, name='generate_case_pdf'),
    path('officer-dashboard/', officer_dashboard, name='officer_dashboard'),
    path('case/<int:case_id>/close/', close_case, name='close_case'),
    path('case/<int:case_id>/delete/', delete_case, name='delete_case'),
    path('book-suspect/', book_suspect, name='book_suspect'),
    path('inmate/<int:inmate_id>/update-status/', update_inmate_status, name='update_inmate_status'),
    path('commander-dashboard/', police_commander_dashboard, name='commander_dashboard'),
    path('view-inventory/', view_inventory, name='view_inventory'),
    path('add-inventory/', add_inventory_item, name='add_inventory_item'),
    path('update-inventory/<int:item_id>/', update_inventory_item, name='update_inventory_item'),
    path('view-rosters/', view_rosters, name='view_rosters'),
    path('add-roster/', add_roster, name='add_roster'),
    path('audit-logs/', system_audit_logs, name='audit_logs'),
    path('evidence/<int:evidence_id>/chain-of-custody/', evidence_chain_of_custody, name='evidence_chain_of_custody'),
    path('suspect/<int:suspect_id>/charge-sheet/', create_charge_sheet, name='create_charge_sheet'),
]