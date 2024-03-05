import argparse
import json
import csv
import tax_lot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", type=str, help="program mode: auto, manual")
    parser.add_argument("input", type=str,
                        help="input file path. "
                             "if mode=auto: gain&loss csv file downloaded from etrade. "
                             "if mode=manual: json file, please refer to included sample-input.json")
    parser.add_argument("output", type=str, help="output file path")
    parser.add_argument("-c", "--cash", type=int, help="vmware share count liquidated for cash")
    parser.add_argument("-s", "--stock", type=int, help="vmware share count liquidated for stock")
    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()

    mode = args.mode
    output_file = open(args.output, "w")

    if args.cash and args.stock:
        tax_lot.update_global_variable(args.cash, args.stock)

    tax_lot.display_global_variable(output_file)
    tax_lot.load_historical_price()
    tax_lot.load_espp_dates()

    if mode == "manual":
        calc_tax_manual(args.input, output_file, args.verbose)
    else:
        calc_tax_auto(args.input, output_file, args.verbose)

    output_file.close()


def calc_tax_manual(input_file_path, output_file, verbose):
    input_file = open(input_file_path)
    lots = json.load(input_file)
    input_file.close()

    for lot in lots:
        output_file.write("\n--------------------------------------------------------------\n")
        calc_lot_tax(lot)
        tax_lot.display_lot_tax(lot, output_file, verbose)


def calc_tax_auto(input_file_path, output_file, verbose):
    lots = []
    idx = 3

    avgo_lot = None
    avgo_fractional_share = None
    avgo_acquire_date = None
    avgo_fractional_share_proceeds = None

    # read in gain&loss csv file
    with open(input_file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        gain_loss_data = [row for row in csv_reader]

    # process each row in csv file
    for row in gain_loss_data:
        if row["Symbol"] == "VMW":
            lot = {"share": int(row["Qty."]), "acquire_date": row["Date Acquired"]}

            # identify unknown type is espp or rs
            plan_type = row["Plan Type"]
            if plan_type == "":
                offer_date = tax_lot.get_espp_offer_date(lot["acquire_date"])
                if offer_date:
                    lot["type"] = "ESPP"
                    lot["offer_date"] = offer_date
                else:
                    lot["type"] = "RS"
            else:
                lot["type"] = plan_type
                if plan_type == "ESPP":
                    lot["offer_date"] = row["Grant Date"]

            # so the per lot tax data in output file can be referred back to corresponding csv row
            lot["row_id"] = idx
            idx = idx + 1

            calc_lot_tax(lot)
            lots.append(lot)
        elif row["Symbol"] == "AVGO":
            # get avgo fractional share info
            avgo_acquire_date = row["Date Acquired"]
            avgo_fractional_share = float(row["Qty."])
            avgo_fractional_share_proceeds = float(row["Total Proceeds"][1:])

    # find the lot used for avgo fractional share cost base, calc avgo fractional share cost base
    if avgo_acquire_date:
        avgo_lot = find_avgo_fractional_lot(avgo_acquire_date, lots)
        avgo_lot["fractional_share"] = avgo_fractional_share
        avgo_lot["fractional_share_proceeds"] = avgo_fractional_share_proceeds
        tax_lot.calc_fractional_share(avgo_lot)

    total_vmw_share = 0
    total_avgo_share = 0
    total_proceeds = 0
    total_long_term_proceeds = 0
    total_long_term_cost_base = 0
    total_long_term_capital_gain = 0
    total_short_term_proceeds = 0
    total_short_term_cost_base = 0
    total_short_term_capital_gain = 0

    # compute tax summary of all lots
    for lot in lots:
        total_vmw_share = total_vmw_share + lot["share"]
        total_avgo_share = total_avgo_share + lot["avgo_share"]
        total_proceeds = total_proceeds + lot["total_proceeds"]

        if lot["long_term"]:
            total_long_term_proceeds = total_long_term_proceeds + lot["total_proceeds"]
            total_long_term_cost_base = total_long_term_cost_base + lot["total_cost_base"]
            total_long_term_capital_gain = total_long_term_capital_gain + lot["total_capital_gain"]
        else:
            total_short_term_proceeds = total_short_term_proceeds + lot["total_proceeds"]
            total_short_term_cost_base = total_short_term_cost_base + lot["total_cost_base"]
            total_short_term_capital_gain = total_short_term_capital_gain + lot["total_capital_gain"]

    # display tax summary of all lots
    output_file.write('{:<35s}{:<.3f}\n'.format("total_vmw_share:", total_vmw_share))
    output_file.write('{:<35s}{:<.3f}\n'.format("total_avgo_share:", total_avgo_share))
    output_file.write('{:<35s}{:<.2f}\n\n'.format("total_proceeds:", total_proceeds))

    output_file.write('{:<35s}{:<.2f}\n'.format("total_short_term_proceeds:", total_short_term_proceeds))
    output_file.write('{:<35s}{:<.2f}\n'.format("total_short_term_cost_base:", total_short_term_cost_base))
    output_file.write('{:<35s}{:<.2f}\n\n'.format("total_short_term_capital_gain:", total_short_term_capital_gain))

    output_file.write('{:<35s}{:<.2f}\n'.format("total_long_term_proceeds:", total_long_term_proceeds))
    output_file.write('{:<35s}{:<.2f}\n'.format("total_long_term_cost_base:", total_long_term_cost_base))
    output_file.write('{:<35s}{:<.2f}\n\n'.format("total_long_term_capital_gain:", total_long_term_capital_gain))

    # display fractional share info, same info is also displayed in that lot
    if "fractional_share" in avgo_lot:
        output_file.write('{:<35s}{:<d}\n'.format("fractional share cost base lot:", avgo_lot["row_id"]))
        output_file.write('{:<35s}{:<s}\n'.format("acquire_date:", avgo_lot["acquire_date"]))
        output_file.write('{:<35s}{:<s}\n'.format("long_term:", str(avgo_lot["long_term"])))
        tax_lot.display_fractiona_share(output_file, avgo_lot)

    # display tax data for each lot
    for lot in lots:
        output_file.write("\n---------------------- row: %d ----------------------\n" % lot["row_id"])
        tax_lot.display_lot_tax(lot, output_file, verbose)


def find_avgo_fractional_lot(avgo_acquire_date, lots):
    for lot in lots:
        if lot["acquire_date"] == avgo_acquire_date:
            return lot


def calc_lot_tax(lot):
    # validate required input is present
    if ("type" not in lot) or ("share" not in lot) or ("acquire_date" not in lot):
        raise Exception("Lot misses required info: type, share, acquire_date")

    if lot["type"] == "ESPP":
        lot["offer_date"] = tax_lot.get_espp_offer_date(lot["acquire_date"])
        tax_lot.calc_espp_cost_base(lot)
    elif lot["type"] == "RS":
        tax_lot.calc_rs_cost_base(lot)
    else:
        if "purchase_price" not in lot:
            raise Exception("PURCHASE type lot misses purchase_price info")
        tax_lot.calc_other_cost_base(lot)

    tax_lot.adjust_special_dividend(lot)
    tax_lot.check_capital_gain_term(lot)
    tax_lot.calc_merge_tax_and_avgo_cost_base(lot)
    tax_lot.calc_total(lot)

    if ("fractional_share" in lot) and ("fractional_share_proceeds" in lot):
        tax_lot.calc_fractional_share(lot)


if __name__ == "__main__":
    main()
