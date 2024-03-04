## Automated Personal Tax Preparing Tool for VMware Acquisition
This is a python based tool aimed at auto generating cost base for current tax year filing and adjust AVGO share 
cost base to ease future tax year filing. It generates tax info for each lot of type ESPP, RSU, PURCHASE for VMW
shares. Also generates tax summary across all lots and AVGO cash in lieu fractional share info.

## USAGE
```text
usage: tax.py [-h] [-c CASH] [-s STOCK] [-v] mode input output

positional arguments:
  mode                      program mode: auto, manual
  input                     input file path 
                            if mode=auto: gain&loss csv file downloaded from etrade
                            if mode=manual: json file, please refer to included sample-input.json
  output                    output file path

options:
  -h, --help                show this help message and exit
  -c CASH, --cash CASH      vmware share count liquidated for cash
  -s STOCK, --stock stock   vmware share count liquidated for stock
  -v, --verbose             increase output verbosity
```

#### Usage example
```text
cd tool-dir
python tax.py auto gain-loss.csv output.txt -c 459 -s 500 -v
python tax.py manual input.json output.txt -c 459 -s 500 -v
```

#### Prepare Input Parameter
- `gain-loss.csv`: download from ETRADE, select `Stock Plan (AVGO) ACCOUNT` -> `My Account` tab -> `Gains & Losses` -> 
click `Download` button. Then, save it in csv format.
- vmware share count liquidated for cash & stock: download 12/31/2023 Single Account Statement from ETRADE, find number on last page

#### Auto Mode
In auto mode, tool processes each row in downloaded Gain & Loss csv file and generates tax info.

#### Manual Mode
In manual mode, input json file contains a set of lot specs, please refer to provided 
sample-input.json. Tool processes each spec and generates tax info. `fractional_share` and `fractional_share_proceeds` fields can be added to spec to
trigger fractional share computation for that lot.

#### Potential AVGO Cost Base Adjustment For Last ESPP Lot
Generated AVGO cost base can be used as is except the last ESPP lot, which is the only one with disqualifying disposition.
If AVGO shares from that lot are sold after 08/31/2024, its ESPP disposition status will be transitioned to qualifying. To reflect this change, we could 
modify `tax_lot.py` file, search for `is_qualifying_disposition` method, hardcode
return value to `Ture`, then rerun the tool.

## License
This repo is free for non-commercial use. If you want to use any of it commercially, please contact me.

## Disclaim
Tool is for information and knowledge sharing purpose. Author is not tax professional, assumes no responsibility or liability for any errors or omissions in the content of this tool.