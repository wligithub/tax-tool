## Automated Personal Tax Preparing Tool for VMware Acquisition
This is a python based tool aimed at auto generating cost base for current tax year filing and adjust AVGO share 
cost base to ease future tax year filing. 

This tool processes Gain & Loss file downloaded from ETRADE. It generates tax info for each row(lot) that is not sold 
before merge. It also generates tax summary across all lots and AVGO cash in lieu fractional share info if applicable.

## USAGE
```text
usage: tax.py [-h] [-c CASH] [-s STOCK] input output

positional arguments:
  input                     gain & loss csv file path
  output                    output file path, without file extension

options:
  -h, --help                show this help message and exit
  -c CASH, --cash CASH      vmware share count liquidated for cash
  -s STOCK, --stock STOCK   vmware share count liquidated for stock
```

#### Usage example
```text
cd tool-dir
python tax.py gain-loss.csv output -c 459 -s 500
```

#### Prepare Input Parameter
- `gain&loss` file: from ETRADE website, select `Stock Plan (AVGO) ACCOUNT` -> `My Account` tab -> `Gains & Losses` -> 
click `Download`. Either `Download Collapsed` or `Download Expanded` are ok. Then, save it in csv format.
- vmware share count liquidated for cash & stock: from ETRADE website, select `Stock Plan (AVGO) ACCOUNT` -> 
`Tax Information` tab -> `statements` -> download 12/31/2023 Single Account Statement. On the last page of this statement:
    - find row with `UNACCEPTED SHARES` comments, the `Quantity` number is the share count liquidated for cash
    - find row with `TENDER PAYMERNT` comments, the `Quantity` number is the share count liquidated for stock
    
#### Output
This tool generates two files that contain computed tax info: one in text format, another with the same name in csv format. In both output files, each lot 
is identified by a row id which refers back to row id of the passed in Gain & Loss file.

#### Turbo Tax Filing
From output file, for each lot that is not sold before merge date,
- enter "total proceeds" value into `Box 1d - Proceeds`
- enter "total cost base" value into `Cost basis or adjusted cost basis`

![Alt text](img/tt-1.png?raw=true "enter total proceeds")
![Alt text](img/tt-2.png?raw=true "enter total cost base")


#### Potential AVGO Cost Base Adjustment For Last ESPP Lot
Generated AVGO cost base can be used as is except the last ESPP lot, which is the only one with disqualifying disposition.
If AVGO shares from that lot are sold after 08/31/2024, its ESPP disposition status will be transitioned to qualifying. To reflect this change, we could 
modify `tax_lot.py` file, search for `is_qualifying_disposition` method, hardcode
return value to `Ture`, then rerun the tool.

## License
This repo is free for non-commercial use. If you want to use any of it commercially, please contact me.

## Disclaim
Tool is for information and knowledge sharing purpose. Author is not tax professional, assumes no responsibility or liability for any errors or omissions in the content of this tool.