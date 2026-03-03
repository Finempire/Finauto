"""Sales Invoice XML generation for Tally."""
import pandas as pd
from html import escape


def create_sales_tally_xml(df, company_name, sgst_ledger="Output SGST@2.5%", cgst_ledger="Output CGST@2.5%", igst_ledger="Output IGST@5%"):
    xml_template = """<ENVELOPE>
 <HEADER>
  <TALLYREQUEST>Import Data</TALLYREQUEST>
 </HEADER>
 <BODY>
  <IMPORTDATA>
   <REQUESTDESC>
    <REPORTNAME>Vouchers</REPORTNAME>
    <STATICVARIABLES>
     <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
    </STATICVARIABLES>
   </REQUESTDESC>
   <REQUESTDATA>
{tally_messages}
   </REQUESTDATA>
  </IMPORTDATA>
 </BODY>
</ENVELOPE>"""

    all_messages = []
    errors = []
    grouped = df.groupby('REFERANCE NO', sort=False)

    for ref_no, group in grouped:
        try:
            first_row = group.iloc[0]
            date_obj = pd.to_datetime(first_row['INVOICE DATE'], dayfirst=True)
            tally_date = date_obj.strftime('%Y%m%d')
            party_name = escape(str(first_row['PARTY A/C NAME']))
            voucher_number = escape(str(ref_no))
            gst_no = str(first_row['GST NO']) if pd.notna(first_row.get('GST NO')) else ''
            place_of_supply = str(first_row['PLACE OF SUPPLY']) if pd.notna(first_row.get('PLACE OF SUPPLY')) else ''

            total_amount = round(group['TOTAL AMOUNT'].sum(), 2)
            total_sgst = round(group['SGST'].sum(), 2) if 'SGST' in group.columns else 0
            total_cgst = round(group['CGST'].sum(), 2) if 'CGST' in group.columns else 0
            total_igst = round(group['IGST'].sum(), 2) if 'IGST' in group.columns else 0
            total_item_amount = round(group['AMOUNT'].sum(), 2)
            computed_total = round(total_item_amount + total_sgst + total_cgst + total_igst, 2)
            round_off = round(total_amount - computed_total, 2)

            extra_tags = ''
            if place_of_supply:
                extra_tags += f'\n      <STATENAME>{escape(place_of_supply)}</STATENAME>'
                extra_tags += f'\n      <COUNTRYOFRESIDENCE>India</COUNTRYOFRESIDENCE>'
                extra_tags += f'\n      <PLACEOFSUPPLY>{escape(place_of_supply)}</PLACEOFSUPPLY>'
            if gst_no:
                extra_tags += f'\n      <PARTYGSTIN>{escape(gst_no)}</PARTYGSTIN>'

            inventory_entries = ''
            for _, item_row in group.iterrows():
                item_name = escape(str(item_row['NAME OF ITEM']))
                quantity = float(item_row['QUANTITY']) if pd.notna(item_row['QUANTITY']) else 0
                rate = round(float(item_row['RATE']), 2) if pd.notna(item_row['RATE']) else 0
                amount = round(float(item_row['AMOUNT']), 2) if pd.notna(item_row['AMOUNT']) else 0
                item_sales_ledger = escape(str(item_row['SALES LEDGER']))
                if quantity == 0 and amount == 0:
                    continue
                inventory_entries += f"""
      <ALLINVENTORYENTRIES.LIST>
       <STOCKITEMNAME>{item_name}</STOCKITEMNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <RATE>{rate}/pcs</RATE>
       <AMOUNT>{amount}</AMOUNT>
       <ACTUALQTY> {quantity:.2f} pcs</ACTUALQTY>
       <BILLEDQTY> {quantity:.2f} pcs</BILLEDQTY>
       <BATCHALLOCATIONS.LIST>
        <GODOWNNAME>Main Location</GODOWNNAME>
        <BATCHNAME>Primary Batch</BATCHNAME>
        <AMOUNT>{amount}</AMOUNT>
        <ACTUALQTY> {quantity:.2f} pcs</ACTUALQTY>
        <BILLEDQTY> {quantity:.2f} pcs</BILLEDQTY>
       </BATCHALLOCATIONS.LIST>
       <ACCOUNTINGALLOCATIONS.LIST>
        <LEDGERNAME>{item_sales_ledger}</LEDGERNAME>
        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
        <AMOUNT>{amount}</AMOUNT>
       </ACCOUNTINGALLOCATIONS.LIST>
      </ALLINVENTORYENTRIES.LIST>"""

            ledger_entries = f"""
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>{party_name}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
       <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
       <AMOUNT>-{total_amount}</AMOUNT>
      </LEDGERENTRIES.LIST>"""

            if total_sgst > 0:
                ledger_entries += f"""
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>{escape(sgst_ledger)}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <AMOUNT>{total_sgst}</AMOUNT>
      </LEDGERENTRIES.LIST>"""
            if total_cgst > 0:
                ledger_entries += f"""
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>{escape(cgst_ledger)}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <AMOUNT>{total_cgst}</AMOUNT>
      </LEDGERENTRIES.LIST>"""
            if total_igst > 0:
                ledger_entries += f"""
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>{escape(igst_ledger)}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
       <AMOUNT>{total_igst}</AMOUNT>
      </LEDGERENTRIES.LIST>"""
            if round_off != 0:
                round_deemed = 'No' if round_off > 0 else 'Yes'
                ledger_entries += f"""
      <LEDGERENTRIES.LIST>
       <LEDGERNAME>Round Off</LEDGERNAME>
       <ISDEEMEDPOSITIVE>{round_deemed}</ISDEEMEDPOSITIVE>
       <AMOUNT>{round_off}</AMOUNT>
      </LEDGERENTRIES.LIST>"""

            voucher_xml = f"""
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Invoice Voucher View">
      <DATE>{tally_date}</DATE>
      <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
      <PARTYNAME>{party_name}</PARTYNAME>
      <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
      <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
      <BASICBASEPARTYNAME>{party_name}</BASICBASEPARTYNAME>
      <PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>
      <VCHENTRYMODE>Item Invoice</VCHENTRYMODE>
      <ISINVOICE>Yes</ISINVOICE>
      <GSTREGISTRATIONTYPE>Unregistered/Consumer</GSTREGISTRATIONTYPE>{extra_tags}
{inventory_entries}
{ledger_entries}
     </VOUCHER>
    </TALLYMESSAGE>"""
            all_messages.append(voucher_xml)
        except Exception as e:
            errors.append(f"Invoice {ref_no}: {str(e)}")

    return xml_template.format(
        company_name=escape(str(company_name)),
        tally_messages='\n'.join(all_messages)
    ), errors


def get_sales_template_csv():
    template_data = {
        'REFERANCE NO': ['SI/25-26/001', 'SI/25-26/001', 'SI/25-26/002'],
        'INVOICE DATE': ['01-01-2026', '01-01-2026', '02-01-2026'],
        'GST NO': ['', '', '29XXXXX1234Z1Z5'],
        'PARTY A/C NAME': ['Customer A', 'Customer A', 'Customer B'],
        'PLACE OF SUPPLY': ['', '', 'Karnataka'],
        'SALES LEDGER': ['Export Sale', 'Export Sale', 'Local Sale'],
        'NAME OF ITEM': ['Item 1', 'Item 2', 'Item 1'],
        'QUANTITY': [10, 5, 20],
        'RATE': [100.00, 200.00, 150.00],
        'AMOUNT': [1000.00, 1000.00, 3000.00],
        'SGST': [0, 0, 135.00],
        'CGST': [0, 0, 135.00],
        'IGST': [0, 0, 0],
        'TOTAL AMOUNT': [1000.00, 1000.00, 3270.00]
    }
    return pd.DataFrame(template_data).to_csv(index=False)
