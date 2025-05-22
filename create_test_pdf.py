"""Create a simple test PDF for demonstration."""

import fitz
from pathlib import Path

def create_test_pdf():
    """Create a multi-document test PDF."""
    doc = fitz.open()
    
    # Document 1: Email
    page1 = doc.new_page()
    text1 = """From: john.doe@contractor.com
To: jane.smith@owner.com
Subject: Project Update - Foundation Work
Date: October 15, 2023

Dear Jane,

This email is to update you on the progress of the foundation work.
We have completed 75% of the concrete pour and expect to finish
by the end of this week.

Best regards,
John Doe
Project Manager"""
    
    page1.insert_text((50, 50), text1, fontsize=12)
    
    # Document 2: Payment Application
    page2 = doc.new_page()
    text2 = """PAYMENT APPLICATION NO. 5
AIA DOCUMENT G702

Project: Office Building Construction
Contractor: ABC Construction LLC
Date: October 20, 2023

Application for Payment Summary:
Original Contract Sum: $2,500,000.00
Net Change by Change Orders: $125,000.00
Contract Sum to Date: $2,625,000.00

Work Completed this Period: $450,000.00
Materials Stored: $50,000.00
Total Completed and Stored: $500,000.00"""
    
    page2.insert_text((50, 50), text2, fontsize=12)
    
    # Document 3: Change Order
    page3 = doc.new_page()
    text3 = """CHANGE ORDER NO. 12
AIA DOCUMENT G701

Project: Office Building Construction
Change Order Date: October 25, 2023

Description of Change:
Addition of decorative lighting in lobby area
including installation and electrical work.

Cost Impact:
Original Contract Sum: $2,625,000.00
This Change Order: $75,000.00
New Contract Sum: $2,700,000.00

Approved by:
Owner: _________________ Date: _______
Contractor: _____________ Date: _______"""
    
    page3.insert_text((50, 50), text3, fontsize=12)
    
    # Document 4: RFI
    page4 = doc.new_page()
    text4 = """REQUEST FOR INFORMATION
RFI NO. 23

Project: Office Building Construction
Date: October 28, 2023
From: ABC Construction LLC
To: XYZ Architects

Subject: Clarification on HVAC Ductwork Routing

Description:
Please clarify the routing of the main HVAC ductwork
in the second floor mechanical room. The plans show
conflicting information between sheets M-3 and M-7.

Response Required By: November 3, 2023

Submitted by:
John Doe, Project Manager
ABC Construction LLC"""
    
    page4.insert_text((50, 50), text4, fontsize=12)
    
    # Save the test PDF
    test_pdf_path = Path("test_construction_docs.pdf")
    doc.save(test_pdf_path)
    doc.close()
    
    print(f"Test PDF created: {test_pdf_path}")
    return test_pdf_path

if __name__ == "__main__":
    create_test_pdf()