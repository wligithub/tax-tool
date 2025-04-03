import argparse
import csv
from datetime import datetime
import tax_lot

FORCE_QUALIFYING_DISPOSITION = False
VMWARE_IPO_DATE = "08/14/2007"
ipo_date = datetime.strptime(VMWARE_IPO_DATE, "%m/%d/%Y")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="gain & loss csv file path")
    parser.add_argument("output", type=str, help="output file path, without file extension")
    parser.add_argument("-c", "--cash", type=int, help="vmware share count liquidated for cash")
    parser.add_argument("-s", "--stock", type=int, help="vmware share count liquidated for stock")
    parser.add_argument("-q", "--qualifying", action="store_true",
                        help="force espp lot to use qualifying disposition, default to false")
    args = parser.parse_args()

    global FORCE_QUALIFYING_DISPOSITION
    if args.qualifying:
        FORCE_QUALIFYING_DISPOSITION = True

    output_file_name = args.output
    output_file = open(output_file_name + ".txt", "w")
    csv_file = open(output_file_name + ".csv", "w")

    print("Output files: %s, %s" % (output_file_name + ".txt", output_file_name + ".csv"))

    if args.cash and args.stock:
        tax_lot.update_global_variable(args.cash, args.stock)

    tax_lot.display_global_variable(output_file)
    tax_lot.load_historical_price()
    tax_lot.load_espp_dates()

    calc_tax(args.input, output_file, csv_file)

    output_file.close()
    csv_file.close()


def calc_tax(input_file_path, output_file, csv_file):
    lots = []
    idx = 1

    fractional_inputs = []
    fractional_lots = []

    # read in gain&loss csv file
    with open(input_file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        gain_loss_data = [row for row in csv_reader]

    # process each row in csv file
    for row in gain_loss_data:
        idx += 1

        if row["Record Type"] != "Sell":
            continue

        if row["Symbol"] == "VMW":
            lot = {"row_id": idx, "share": float(row["Qty."]), "acquire_date": sanitize_date_str(row["Date Acquired"])}

            acquired_date = datetime.strptime(lot["acquire_date"], "%m/%d/%Y")
            if acquired_date < ipo_date:
                print("Acquired date before VMware IPO, acquired date=%s, row id=%d" % (
                    lot["acquire_date"], lot["row_id"]))
                continue

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
                    lot["offer_date"] = tax_lot.get_espp_offer_date(lot["acquire_date"])
                elif plan_type == "BUY":
                    lot["purchase_price"] = float(row["Acquisition Cost"].strip("$").strip()
                                                  .replace(",", "")) / lot["share"]

            if (not lot["type"] == "ESPP" and not lot["type"] == "RS" and not lot["type"] == "SO" and
                    not lot["type"] == "BUY"):
                print("Unsupported lot, type=%s, row id=%d" % (lot["type"], lot["row_id"]))
                continue

            lot["sold_date"] = sanitize_date_str(row["Date Sold"])

            # so we know which lot is sold before merge
            tax_lot.set_lot_merge_status(lot)
            lot["total_proceeds"] = float(row["Total Proceeds"].strip("$").strip().replace(",", ""))

            calc_lot_tax(lot)
            lots.append(lot)
        elif row["Symbol"] == "AVGO":
            sold_date_str = sanitize_date_str(row["Date Sold"])

            # only look for avgo fractional sell lot, skip avgo lot sold after merge
            if sold_date_str == tax_lot.MERGE_DATE:
                # get avgo fractional share info
                avgo_acquire_date = sanitize_date_str(row["Date Acquired"])
                avgo_fractional_share = float(row["Qty."])
                avgo_fractional_share_proceeds = float(row["Total Proceeds"].strip("$").strip().replace(",", ""))

                fractional_input = {"avgo_acquire_date": avgo_acquire_date,
                                    "avgo_fractional_share": avgo_fractional_share,
                                    "avgo_fractional_share_proceeds": avgo_fractional_share_proceeds}
                fractional_inputs.append(fractional_input)
            else:
                print("Sold AVGO after merge date, row id=%d, share=%.3f" % (idx, float(row["Qty."])))

    # find the lot used for avgo fractional share cost base, calc avgo fractional share cost base
    for fractional_input in fractional_inputs:
        fractional_lot = find_avgo_fractional_lot(fractional_input["avgo_acquire_date"], lots)

        if fractional_lot is not None:
            fractional_lot["fractional_share"] = fractional_input["avgo_fractional_share"]
            fractional_lot["fractional_share_proceeds"] = fractional_input["avgo_fractional_share_proceeds"]
            tax_lot.calc_fractional_share(fractional_lot)
            fractional_lots.append(fractional_lot)
        else:
            print("Failed to find cost base lot for fractional share, acquire date=%s" % fractional_input[
                "avgo_acquire_date"])

    compute_and_display_tax_summary(output_file, lots, fractional_lots)

    # display tax data for each lot
    tax_lot.generate_csv_header(csv_file)
    for lot in lots:
        output_file.write("\n---------------------- row: %d ----------------------\n" % lot["row_id"])
        tax_lot.display_lot_tax(lot, output_file, csv_file)


def sanitize_date_str(date_str):
    slash_position = date_str.rfind("/")
    year_len = len(date_str) - slash_position - 1

    if year_len == 2:
        tmp_date = datetime.strptime(date_str, "%m/%d/%y")
    else:
        tmp_date = datetime.strptime(date_str, "%m/%d/%Y")

    return datetime.strftime(tmp_date, "%m/%d/%Y")


def calc_lot_tax(lot):
    if lot["type"] == "ESPP":
        tax_lot.calc_espp_cost_base(lot, FORCE_QUALIFYING_DISPOSITION)
    else:
        tax_lot.calc_cost_base(lot)

    tax_lot.adjust_special_dividend(lot)
    tax_lot.set_capital_gain_term(lot)

    if lot["merged"]:
        tax_lot.calc_merge_tax_and_avgo_cost_base(lot)
    else:
        tax_lot.calc_not_merged_tax(lot)


def find_avgo_fractional_lot(avgo_acquire_date, lots):
    # e*trade uses the last lot with matching date as the fractional lot
    for lot in reversed(lots):
        if lot["acquire_date"] == avgo_acquire_date and lot["merged"]:
            return lot

    return None


def compute_and_display_tax_summary(output_file, lots, fractional_lots):
    total_vmw_share = 0
    total_avgo_share = 0
    total_long_term_proceeds = 0
    total_long_term_cost_base = 0
    total_long_term_capital_gain = 0
    total_short_term_proceeds = 0
    total_short_term_cost_base = 0
    total_short_term_capital_gain = 0
    total_fractional_share_cost_base = 0
    total_fractional_share_capital_gain = 0

    # compute tax summary of all lots
    for lot in lots:
        total_vmw_share += lot["share"]

        if lot["long_term"]:
            total_long_term_proceeds += lot["total_proceeds"]
            total_long_term_cost_base += lot["filing_cost_base"]
            total_long_term_capital_gain += lot["total_capital_gain"]
        else:
            total_short_term_proceeds += lot["total_proceeds"]
            total_short_term_cost_base += lot["filing_cost_base"]
            total_short_term_capital_gain += lot["total_capital_gain"]

        if lot["merged"]:
            total_avgo_share += lot["avgo_share"]

    total_proceeds = total_long_term_proceeds + total_short_term_proceeds

    # compute fractional share summary
    for fractional_lot in fractional_lots:
        total_fractional_share_cost_base += fractional_lot["fractional_share_cost_base"]
        total_fractional_share_capital_gain += fractional_lot["fractional_share_capital_gain"]
        total_proceeds += fractional_lot["fractional_share_proceeds"]

    # display tax summary of all lots
    output_file.write('{:<35s}{:<.3f}\n'.format("total vmw share:", total_vmw_share))
    output_file.write('{:<35s}{:<.3f}\n'.format("total avgo share:", total_avgo_share))
    output_file.write('{:<35s}${:,.2f}\n\n'.format("total proceeds:", total_proceeds))

    output_file.write('{:<35s}${:,.2f}\n'.format("total short term proceeds:", total_short_term_proceeds))
    output_file.write('{:<35s}${:,.2f}\n'.format("total short term cost basis:", total_short_term_cost_base))
    output_file.write(
        '{:<35s}${:,.2f}\n\n'.format("total short term capital gain:", total_short_term_capital_gain))

    output_file.write('{:<35s}${:,.2f}\n'.format("total long term proceeds:", total_long_term_proceeds))
    output_file.write('{:<35s}${:,.2f}\n'.format("total long term cost basis:", total_long_term_cost_base))
    output_file.write('{:<35s}${:,.2f}\n\n'.format("total long term capital gain:", total_long_term_capital_gain))

    output_file.write(
        '{:<50s}${:,.2f}\n'.format("total avgo cash-in-lieu frac share cost basis:", total_fractional_share_cost_base))
    output_file.write(
        '{:<50s}${:,.2f}\n'.format("total avgo cash-in-lieu frac share capital gain:",
                                   total_fractional_share_capital_gain))

    # display fractional share info, same info is also displayed in that lot
    for fractional_lot in fractional_lots:
        output_file.write('\n{:<35s}{:<d}\n'.format("fractional share cost basis lot:", fractional_lot["row_id"]))
        output_file.write('{:<35s}{:<s}\n'.format("acquire date:", fractional_lot["acquire_date"]))
        output_file.write('{:<35s}{:<s}'.format("long term:", str(fractional_lot["long_term"])))
        tax_lot.display_fractional_share(output_file, fractional_lot)


if __name__ == "__main__":
    main()
