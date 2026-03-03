"""Bank statement XML generation for Tally."""
import pandas as pd
from html import escape


def create_bank_tally_xml(df, bank_ledger, company_name):
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

    voucher_template = """
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER VCHTYPE="{voucher_type}" ACTION="Create">
      <DATE>{date}</DATE>
      <VOUCHERTYPENAME>{voucher_type}</VOUCHERTYPENAME>
      <NARRATION>{narration}</NARRATION>
      <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
      {ledger_entries}
     </VOUCHER>
    </TALLYMESSAGE>"""

    ledger_entry_template = """
      <ALLLEDGERENTRIES.LIST>
       <LEDGERNAME>{ledger_name}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>{is_positive}</ISDEEMEDPOSITIVE>
       <AMOUNT>{amount}</AMOUNT>
      </ALLLEDGERENTRIES.LIST>"""

    all_messages = []
    errors = []

    for index, row in df.iterrows():
        narration = 'N/A'
        try:
            date_obj = pd.to_datetime(row['Date'], dayfirst=True)
            tally_date = date_obj.strftime('%Y%m%d')
            narration = str(row['Narration'])
            debit = round(float(row['Debit']), 2)
            credit = round(float(row['Credit']), 2)
            mapped_ledger = row['Mapped Ledger']

            if debit > 0:
                voucher_type = 'Payment'
                bank_amount = debit
                contra_amount = debit * -1
                is_bank_positive = 'No'
                is_contra_positive = 'Yes'
            elif credit > 0:
                voucher_type = 'Receipt'
                bank_amount = credit * -1
                contra_amount = credit
                is_bank_positive = 'Yes'
                is_contra_positive = 'No'
            else:
                continue

            narration_safe = escape(str(narration)) if pd.notna(narration) else 'N/A'
            bank_ledger_safe = escape(str(bank_ledger))
            mapped_safe = escape(str(mapped_ledger))

            ledger_list = []
            bank_entry = ledger_entry_template.format(
                ledger_name=bank_ledger_safe, is_positive=is_bank_positive, amount=bank_amount
            )
            ledger_list.append((bank_entry, is_bank_positive == 'Yes'))
            contra_entry = ledger_entry_template.format(
                ledger_name=mapped_safe, is_positive=is_contra_positive, amount=contra_amount
            )
            ledger_list.append((contra_entry, is_contra_positive == 'Yes'))
            ledger_list.sort(key=lambda x: not x[1])
            sorted_entries = '\n'.join([e[0] for e in ledger_list])

            all_messages.append(voucher_template.format(
                voucher_type=voucher_type, date=tally_date,
                narration=narration_safe, ledger_entries=sorted_entries
            ))
        except Exception as e:
            errors.append(f"Row {index} ('{narration}'): {str(e)}")

    return xml_template.format(
        company_name=escape(str(company_name)),
        tally_messages='\n'.join(all_messages)
    ), errors


def get_bank_template_csv():
    headers = 'Date,Narration,Debit,Credit\n'
    data = '01-04-2024,Rent Paid to Landlord,50000,0\n'
    data += '02-04-2024,Cash Deposit,0,100000\n'
    data += '05-04-2024,Amazon Office Supplies,15000,0\n'
    return headers + data
