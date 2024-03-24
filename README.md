## Automated Personal Tax Preparing Tool for VMW-AVGO Merger

This is a Python-based tool that automatically calculates the cost basis of the VMW-AVGO merger. It can generate all
data without the need for manually inputting per-lot information; you just need to download two files from E*Trade.

This tool processes the Gain&Loss file downloaded from E*TRADE. For each row (lot), it generates tax information,
including the cost basis for cash received during the merger as well as for converted AVGO shares. Additionally,
it calculates the cost basis for AVGO cash-in-lieu fractional shares and provides a tax summary across all lots.

The tool supports VMW shares acquired via ESPP, RSU, NSO, and brokerage purchases, as well as VMW shares sold before
and on the merger date.

Note:
This tool is applicable only to US holders of VMware shares. It appears that non-US holders have received the cash
component as a dividend instead of a share sale, leading to substantially different implications for tax computation.

## USAGE

```text
usage: tax.py [-h] [-c CASH] [-s STOCK] [-q] input output

positional arguments:
  input                     gain&loss csv file path
  output                    output file path, without file extension

options:
  -h, --help                show this help message and exit
  -c CASH, --cash CASH      vmware share count liquidated for cash
  -s STOCK, --stock STOCK   vmware share count liquidated for stock
  -q, --qualifying          force espp lot to use qualifying disposition, default to false
```

#### Usage example

```text
cd tax-tool
python3 tax.py gain-loss.csv output -c 459 -s 500 -q
```

#### Prepare Input Parameter

- Gain&Loss file: from E*TRADE website, select `Stock Plan (AVGO) ACCOUNT` -> `My Account` tab -> `Gains&Losses` ->
  click `Download`. Either `Download Collapsed` or `Download Expanded` are ok.
    - A xlsx file will be downloaded.
    - Open it in Excel, Numbers, or Google Sheets and save/download it as a CSV file. Choose the
      `Comma Separated Values` option if applicable.
    - If you're using macOS, use Numbers instead of Microsoft Excel to export the .xlsx file as a CSV.
- VMware share count liquidated for cash & stock: from E*TRADE website, select `Stock Plan (AVGO) ACCOUNT` ->
  `Tax Information` tab -> `statements` -> download 12/31/2023 `Single Account Statement`. On the last page of this
  statement:
    - find row with `UNACCEPTED SHARES` comments, the `Quantity` number is the share count liquidated for cash
    - find row with `TENDER PAYMERNT` comments, the `Quantity` number is the share count liquidated for stock
- `-q` option: please refer to the section titled `Potential AVGO Cost Base Adjustment For Last ESPP Lot`

#### Output

This tool generates two files: one in text format and another with the same name in CSV format. Both files contain tax
information for each lot. Additionally, the text file contains cost basis for AVGO cash-in-lieu fractional shares and
provides a tax summary across all lots. In the generated files, each lot has a "Row ID" field, which corresponds to the
ID of the corresponding row from the Gain&Loss input file. This correlation allows for easy matching between computed
lots from the output and reported lots from the input.

#### Gain&Loss File Fields Consumed by Script

Although the Gain&Loss file contains many fields, the script only utilizes the following fields:

- Record Type: `Sell`
- Symbol: `VMW` | `AVGO`
- Plan Type: `ESPP` | `RS` | `SO`
- QTY.: `<number of shares>`
- Date Acquired: `<vest or purchase date>`
- Date Sold: `<date sold>`
- Total Proceeds: `<total proceeds>`

#### Potential AVGO Cost Base Adjustment For Last ESPP Lot

The generated AVGO cost basis can be used as is, except for the last ESPP lot acquired on 08/31/2022, which is the
only one with a disqualifying disposition as of the merge date. Its ESPP disposition status will transition to
qualifying after 03/01/2024. If you didn't sell the converted AVGO shares of that lot before 03/01/2024, include `-q`
as a command line input, which will force the ESPP to be considered as a qualifying disposition. This adjustment will
result in AVGO shares of this lot having a more favorable (higher) cost basis.

#### Handle VMW Shares Acquired Through Brokerage Purchase (Advanced Usage)

VMW shares acquired through brokerage purchases will not be included in the downloaded Gain&Loss file. Users can
create their own Gain & Loss file by making a copy of the downloaded one and wiping out the existing content except
for the header. Then, manually enter purchase information into this new Gain & Loss file, allocating one row per
transaction. Please refer to the section titled `Gain & Loss Fields Consumed by Script` for fields that need to
be populated. Please set `Plan Type` to `BUY` and populate one additional field:

- Plan Type: `BUY`
- Acquisition Cost: `<total purchase price including commission>`

If there is an associated AVGO fractional share sell, add a row with the following fields populated

- Record Type: `Sell`
- Symbol: `AVGO`
- QTY.: `<fractional share number>`
- Date Acquired: `<The acquisition date of the above-added VMW lot for AVGO fractional share cost basis calculation>`.
- Date Sold: `11/22/2023`
- Total Proceeds: `<total proceeds>`

The command-line inputs `-c` and `-s` are used to calculate the precise cash/stock allocation ratio. If you can
determine the `-c` and `-s` values, enter them in the command line as usual. Otherwise, you can skip these optional
parameters, and the script will use the default ratio of 0.479 for cash and 0.521 for stock, respectively.
The `-q` option is not needed, as these are not ESPP shares.

## Turbo Tax Filing

For each stock transaction reported on Form 1099-B, locate the corresponding row (lot) in the generated tax file by
acquisition date and share count.

- Use `Box 1d Proceeds` value generated by script to populate Turbo Tax `Box 1d - Proceeds` field. If you already
  imported from E*TRADE, verify value generated by script matches imported one.
- Use `Filing Cost Basis` value generated by script to populate Turbo Tax `Cost basis or adjusted cost basis` field

![Alt text](img/tt-1.png?raw=true "enter total proceeds")
![Alt text](img/tt-2.png?raw=true "enter total cost base")

## Frequently Asked Questions

#### [Q] My lot cost base is still 0, is this expected? <br />

Yes, the merge transaction is different from a normal sale. In general, if the VMW cost basis is lower than $128
per share, the cost basis is 0. Please refer to the following link for guidelines on computing the
`filing cost base`: https://investors.broadcom.com/static-files/7720c4c1-c940-4d9d-800c-66819bfdc7a0,
Page 3, 2nd to the last paragraph.

#### [Q] How do I correct the share acquisition date listed as 1970 in my lot? <br/>

VMware IPOed on August 14, 2007. It's evident that shares acquired in 1970 are incorrect. Please contact E*TRADE to
rectify this issue. In the meantime, if you know the share acquisition date from this lot (row), please update the
Gain&Loss file to set the `Date Acquired` field to the correct value. Also, ensure that the values of other fields
mentioned in the section 'Gain&Loss File Fields Consumed by Script' are correct, and update them if needed. Then,
rerun the tool.

## Reference

https://investors.broadcom.com/financial-information/tax-information

## License

This repository is free for non-commercial use. If you intend to use any part of it commercially, please reach out to
me for further discussion.

## Disclaim

The tool is intended for informational and knowledge-sharing purposes only. The author is not a tax professional and
assumes no responsibility or liability for any errors or omissions in the content of this tool.