"""
DocuCloud AI - Test Document Suite Generator
--------------------------------------------
Generates 6 distinct test PDF documents covering different cloud triage paths,
financial categories, itemized tables, and anomaly scenarios.
"""

import os
import pymupdf

OUTPUT_DIR = "tests/test_documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_receipt_starbucks():
    """Single page coffee receipt (Meals & Entertainment)."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=550)
    
    page.insert_text((110, 50), "STARBUCKS COFFEE #1042", fontsize=14, fontname="helv", color=(0, 0.4, 0.2))
    page.insert_text((120, 75), "Pike Place, Seattle, WA", fontsize=10)
    page.insert_text((130, 95), "Date: Oct 20, 2026", fontsize=9)
    page.insert_text((125, 110), "Receipt: #SBX-99214", fontsize=9)
    page.draw_line((40, 130), (360, 130), color=(0.7, 0.7, 0.7), width=1)
    
    # Items
    page.insert_text((50, 160), "1x Caffe Latte (Grande)", fontsize=10)
    page.insert_text((300, 160), "$5.45", fontsize=10)
    page.insert_text((50, 190), "1x Caramel Macchiato", fontsize=10)
    page.insert_text((300, 190), "$5.95", fontsize=10)
    page.insert_text((50, 220), "1x Butter Croissant", fontsize=10)
    page.insert_text((300, 220), "$3.35", fontsize=10)
    
    page.draw_line((40, 250), (360, 250), color=(0.7, 0.7, 0.7), width=1)
    page.insert_text((50, 280), "Subtotal:", fontsize=10)
    page.insert_text((300, 280), "$14.75", fontsize=10)
    page.insert_text((50, 305), "Sales Tax (8.5%):", fontsize=10)
    page.insert_text((300, 305), "$1.25", fontsize=10)
    page.insert_text((50, 340), "TOTAL AMOUNT DUE:", fontsize=12, fontname="helv", color=(0, 0, 0))
    page.insert_text((290, 340), "$16.00", fontsize=12, fontname="helv", color=(0, 0, 0))
    
    doc.save(os.path.join(OUTPUT_DIR, "01_starbucks_meals_receipt.pdf"))
    doc.close()

def create_flight_delta():
    """Single page travel flight invoice (Travel & Lodging)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=700)
    
    page.insert_text((50, 60), "DELTA AIR LINES INC.", fontsize=18, fontname="helv", color=(0.8, 0.1, 0.1))
    page.insert_text((50, 85), "Passenger Electronic Ticket & Flight Itinerary", fontsize=11, color=(0.4, 0.4, 0.4))
    
    page.insert_text((50, 130), "Passenger: Anshul Gupta", fontsize=11)
    page.insert_text((50, 150), "Booking Reference / PNR: DL-884920", fontsize=11)
    page.insert_text((50, 170), "Date of Issue: October 18, 2026", fontsize=11)
    page.insert_text((50, 190), "Route: JFK (New York) -> SEA (Seattle)", fontsize=11)
    
    page.draw_rect(pymupdf.Rect(50, 220, 545, 340), color=(0.8, 0.8, 0.8), fill=(0.96, 0.96, 0.98))
    page.insert_text((70, 250), "Base Fare (Main Cabin Class H):", fontsize=11)
    page.insert_text((450, 250), "$390.00", fontsize=11)
    page.insert_text((70, 280), "US Transportation Tax & Security Fees:", fontsize=11)
    page.insert_text((450, 280), "$42.50", fontsize=11)
    page.insert_text((70, 310), "Checked Baggage Priority:", fontsize=11)
    page.insert_text((450, 310), "$50.00", fontsize=11)
    
    page.insert_text((70, 380), "TOTAL FARE CHARGED:", fontsize=14, fontname="helv", color=(0, 0.2, 0.6))
    page.insert_text((430, 380), "$482.50", fontsize=14, fontname="helv", color=(0, 0.2, 0.6))
    
    doc.save(os.path.join(OUTPUT_DIR, "02_delta_travel_ticket.pdf"))
    doc.close()

def create_office_staples():
    """Single page office supplies receipt (Office Supplies)."""
    doc = pymupdf.open()
    page = doc.new_page(width=500, height=650)
    
    page.insert_text((50, 60), "STAPLES BUSINESS DEPOT", fontsize=16, fontname="helv", color=(0.8, 0, 0))
    page.insert_text((50, 85), "Office & Workspace Solutions", fontsize=10, color=(0.4, 0.4, 0.4))
    page.insert_text((50, 120), "Store #412 - Bellevue, WA", fontsize=10)
    page.insert_text((50, 140), "Transaction Date: October 21, 2026", fontsize=10)
    
    page.insert_text((50, 180), "3x Multipurpose Copy Paper (500 Sheets)", fontsize=10)
    page.insert_text((380, 180), "$24.99", fontsize=10)
    page.insert_text((50, 210), "1x Gel Ink Pens Pack (12-Count)", fontsize=10)
    page.insert_text((380, 210), "$14.50", fontsize=10)
    page.insert_text((50, 240), "1x Ergonomic Desk Wrist Rest", fontsize=10)
    page.insert_text((380, 240), "$22.00", fontsize=10)
    
    page.insert_text((50, 300), "Sales Tax:", fontsize=10)
    page.insert_text((380, 300), "$5.20", fontsize=10)
    page.insert_text((50, 330), "TOTAL AMOUNT PAID:", fontsize=12, fontname="helv")
    page.insert_text((370, 330), "$66.69", fontsize=12, fontname="helv")
    
    doc.save(os.path.join(OUTPUT_DIR, "03_staples_office_supplies.pdf"))
    doc.close()

def create_suspicious_high_value_invoice():
    """High value expense triggering anomaly compliance check (> $500)."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=650)
    
    page.insert_text((50, 60), "ELITE EXECUTIVE JEWELRY & WATCHES", fontsize=16, fontname="helv", color=(0.6, 0.4, 0))
    page.insert_text((50, 85), "VIP Client Luxury Goods Invoice", fontsize=10)
    page.insert_text((50, 120), "Invoice #: VIP-2026-004", fontsize=11)
    page.insert_text((50, 140), "Date: October 22, 2026", fontsize=11)
    
    page.insert_text((50, 190), "1x Swiss Luxury Gold Chronograph Wristwatch", fontsize=11)
    page.insert_text((450, 190), "$3,200.00", fontsize=11)
    page.insert_text((50, 220), "1x Leather Presentation Box & Polish Kit", fontsize=11)
    page.insert_text((450, 220), "$250.00", fontsize=11)
    
    page.insert_text((50, 290), "TOTAL AMOUNT DUE:", fontsize=14, fontname="helv", color=(0.8, 0, 0))
    page.insert_text((430, 290), "$3,450.00", fontsize=14, fontname="helv", color=(0.8, 0, 0))
    
    doc.save(os.path.join(OUTPUT_DIR, "04_high_value_anomaly_alert.pdf"))
    doc.close()

def create_heavy_7_page_contract():
    """Heavy multi-page document (7 pages) triggering SQS + EC2 Worker triage."""
    doc = pymupdf.open()
    for i in range(1, 8):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 60), f"EQUINIX GLOBAL DATA CENTER LEASE AGREEMENT - PAGE {i} OF 7", fontsize=13, fontname="helv", color=(0, 0.2, 0.5))
        page.insert_text((50, 90), "Contract Ref: EQX-DC-WEST-2026-7781", fontsize=10, color=(0.4, 0.4, 0.4))
        
        if i == 1:
            page.insert_text((50, 140), "Master Services & Colocation Master Agreement", fontsize=12, fontname="helv")
            page.insert_text((50, 170), "Vendor: Equinix Infrastructure Operations Inc.", fontsize=11)
            page.insert_text((50, 195), "Customer: Acme Enterprise Systems Global", fontsize=11)
            page.insert_text((50, 220), "Contract Effective Date: October 22, 2026", fontsize=11)
            page.insert_text((50, 260), "1. RECITALS & PURPOSE OF COLOCATION FACILITIES", fontsize=11, fontname="helv")
            page.insert_text((50, 290), "This Master Agreement governs the deployment of high-density server racks,", fontsize=10)
            page.insert_text((50, 310), "redundant dual-feed 3-phase power delivery, and multi-carrier cross-connects.", fontsize=10)
        elif i < 7:
            page.insert_text((50, 140), f"SECTION {i}. TECHNICAL & INFRASTRUCTURE SPECIFICATIONS", fontsize=12, fontname="helv")
            page.insert_text((50, 170), f"- Rack Pod {i}A: 42U Enclosure with N+2 Redundant Power Feeds", fontsize=10)
            page.insert_text((50, 200), f"- Dedicated Fiber Cross-Connect Bandwidth (100 Gbps): Standard Tier", fontsize=10)
            page.insert_text((50, 230), f"- Environmental Biometric Access Control & 24/7 Security Operations", fontsize=10)
        else:
            page.insert_text((50, 140), "FINAL PAYMENT SCHEDULE & AUTHORIZATION SIGNATURES", fontsize=12, fontname="helv")
            page.insert_text((50, 180), "Monthly Recurring Colocation Fee: $7,800.00", fontsize=11)
            page.insert_text((50, 210), "State Energy & Utility Surcharge: $950.00", fontsize=11)
            page.insert_text((50, 260), "TOTAL AMOUNT DUE: $8,750.00", fontsize=15, fontname="helv", color=(0.1, 0.6, 0.2))
            page.insert_text((50, 320), "Authorized Signatory: Harrison Ford, Chief Operations Officer", fontsize=10)
            
    doc.save(os.path.join(OUTPUT_DIR, "05_heavy_7_page_contract.pdf"))
    doc.close()

if __name__ == "__main__":
    create_receipt_starbucks()
    create_flight_delta()
    create_office_staples()
    create_suspicious_high_value_invoice()
    create_heavy_7_page_contract()
    print("Successfully generated all 5 diverse test documents in tests/test_documents/!")
