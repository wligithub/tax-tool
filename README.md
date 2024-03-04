## Automated Personal Tax Preparing Tool for VMware Acquisition
This is a python based tool aimed at auto generating cost base for current tax year filing and adjust AVGO share 
cost base to ease future tax year filing. It generates tax info for each lot of type ESPP, RSU or self purchased VMW
shares. Also generates tax summary across all lots and AVGO cash in lieu fractional share info.

## USAGE
```text
usage: tax.py [-h] [-c CASH] [-s STOCK] [-v] mode input output

positional arguments:
  mode                      program mode: auto, manual
  input                     input file path. 
                            if mode=auto: gain&loss csv file downloaded from etrade. 
                            if mode=manual: json file, please refer to included sample-input.json as example
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
- `gain-loss.csv`: download from ETRADE. select `Stock Plan (AVGO) ACCOUNT` -> `My Account` tab -> `Gains & Losses` -> 
click `Download` button. Then, save it in `csv` format.
- vmware share count liquidated for cash & stock: download `12/31/2023 Single Account Statement` from ETRADE, find number on last page

#### Auto Mode
In auto mode, tool processes each row in downloaded Gain & Loss csv and and generates tax info.

#### Manual Mode
In manual mode, tool processes each lot from input json file and generates tax info. This is mainly used for
computing tax info for self purchased VMW shares. Please refer to provided `sample-input.json` for example.

## AVGO Cost Base Adjustment
The generated per lot AVGO shares cost base can be used as is except the latest ESPP lot. That lot is the only one with disqualifying disposition.
If that lot is sold after 08/31/2024, the ESPP disposition status will be transitioned to qualifying. We need to
rerun the tool again to include this change. The easiest way is to modify tax_lot.py file. On top of this file, change the `MERGE_DATE`
to lot sold date, run program again using manual mode with input json file similar to following:
```text
[
   {
      "type":"ESPP",
      "share":<share-number>,
      "acquire_date":"08/31/2022"
   }
]
```

## License
This repo is free for non-commercial use. If you want to use any of it commercially, contact me.

## Disclaim
Author is not tax professional, assumes no responsibility or liability for any errors or omissions in the content of this tool.