"""Journal XML generation for Tally."""
import pandas as pd
from html import escape


def create_tally_xml(df, fixed_ledger_config, dynamic_ledger_config, company_name, voucher_type, journal_mappings):
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

    tally_message_template = """
    <TALLYMESSAGE xmlns:UDF="TallyUDF">
     <VOUCHER VCHTYPE="{voucher_type}" ACTION="Create">
      <DATE>{date}</DATE>
      <VOUCHERTYPENAME>{voucher_type}</VOUCHERTYPENAME>
      <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
      <NARRATION>{narration}</NARRATION>
      <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
      {ledger_entries}
     </VOUCHER>
    </TALLYMESSAGE>"""

    ledger_line_template = """
      <ALLLEDGERENTRIES.LIST>
       <LEDGERNAME>{ledger_name}</LEDGERNAME>
       <ISDEEMEDPOSITIVE>{is_positive}</ISDEEMEDPOSITIVE>
       <AMOUNT>{amount}</AMOUNT>
      </ALLLEDGERENTRIES.LIST>"""

    all_messages = []
    mapping_dicts = {}
    for col_name, mapping_df in journal_mappings.items():
        mapping_dicts[col_name] = pd.Series(mapping_df['Mapped Ledger'].values, index=mapping_df['CSV Value']).to_dict()

    errors = []
    for index, row in df.iterrows():
        try:
            date_obj = pd.to_datetime(row['Date'], dayfirst=True)
            tally_date = date_obj.strftime('%Y%m%d')
            ledger_entries_list = []
            voucher_number = str(row['Voucher Number']) if pd.notna(row['Voucher Number']) else ''

            for ledger in fixed_ledger_config:
                if ledger['CSV Column Name'] in row and pd.notna(row[ledger['CSV Column Name']]):
                    amount_val = round(float(row[ledger['CSV Column Name']]), 2)
                    if amount_val == 0:
                        continue
                    is_positive_flag = 'No' if ledger['Type (Debit/Credit)'] == 'Credit' else 'Yes'
                    amount_for_xml = amount_val if ledger['Type (Debit/Credit)'] == 'Credit' else amount_val * -1
                    ledger_xml = ledger_line_template.format(
                        ledger_name=escape(str(ledger['Tally Ledger Name'])),
                        is_positive=is_positive_flag,
                        amount=amount_for_xml
                    )
                    ledger_entries_list.append((ledger_xml, ledger['Type (Debit/Credit)']))

            for dyn_ledger in dynamic_ledger_config:
                name_col = dyn_ledger['CSV Column for Ledger Name']
                amount_col = dyn_ledger['CSV Column for Amount']
                trans_type = dyn_ledger['Transaction Type']
                if name_col not in row.index or amount_col not in row.index:
                    continue
                csv_value = row[name_col]
                if pd.isna(row[amount_col]):
                    continue
                amount_from_col = round(float(row[amount_col]), 2)
                if pd.notna(csv_value) and str(csv_value).strip() != '' and amount_from_col != 0:
                    current_map = mapping_dicts.get(name_col, {})
                    final_ledger = current_map.get(str(csv_value), str(csv_value))
                    is_positive_flag = 'No' if trans_type == 'Credit' else 'Yes'
                    amount_for_xml = amount_from_col if trans_type == 'Credit' else amount_from_col * -1
                    ledger_xml = ledger_line_template.format(
                        ledger_name=escape(str(final_ledger)),
                        is_positive=is_positive_flag,
                        amount=amount_for_xml
                    )
                    ledger_entries_list.append((ledger_xml, trans_type))

            if ledger_entries_list:
                ledger_entries_list.sort(key=lambda x: 0 if x[1] == 'Debit' else 1)
                final_entries = '\n'.join([e[0] for e in ledger_entries_list])
                narration_raw = row.get('Narration', 'N/A')
                narration_safe = escape(str(narration_raw)) if pd.notna(narration_raw) else 'N/A'
                all_messages.append(tally_message_template.format(
                    voucher_type=voucher_type,
                    date=tally_date,
                    voucher_number=voucher_number,
                    narration=narration_safe,
                    ledger_entries=final_entries
                ))
        except Exception as e:
            errors.append(f"Row {index}: {str(e)}")

    return xml_template.format(
        company_name=escape(str(company_name)),
        tally_messages='\n'.join(all_messages)
    ), errors


def get_template_csv(fixed_ledger_config, dynamic_ledger_config):
    headers = ['Date', 'Voucher Number', 'Narration']
    example = ['01-04-2024', 'SJV-1', 'Salary for April 2024']
    for i, ledger in enumerate(fixed_ledger_config):
        headers.append(ledger['CSV Column Name'])
        example.append(str(1000 * (i + 1)))
    for i, dyn in enumerate(dynamic_ledger_config):
        headers.append(dyn['CSV Column for Ledger Name'])
        example.append(f'Dynamic Ledger {i + 1} Name')
        headers.append(dyn['CSV Column for Amount'])
        example.append(str(5000 * (i + 1)))
    return ','.join(headers) + '\n' + ','.join(example) + '\n'
